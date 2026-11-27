import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.core.rate_limit import (
    KEY_PREFIX_LOGIN,
    KEY_PREFIX_REGISTER,
    LOGIN_IDENTITY_LIMIT,
    REGISTER_IDENTITY_LIMIT,
    check_limit,
    identity_key,
    limiter,
)
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User, UserRole
from app.schemas.auth import LoginRequest, StaffLoginRequest, Token
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["authentication"])


def _is_bcrypt_hash(value: str | None) -> bool:
    """Devuelve True si el valor tiene forma de hash bcrypt ($2b$)."""
    return bool(value) and value.startswith("$2b$")


@router.post("/login/access-token", response_model=Token)
@limiter.limit("5/minute")
async def login(
    request: Request,
    credentials: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Token:
    """Login endpoint - authenticate user and return access token.

    Rate limit: 5 requests per minute to prevent brute force attacks.
    Identity limit: 5 requests per minute per normalized DNI, so the same DNI
    from different clients/IPs exhausts its own counter.
    """
    # --- Check de identidad en frontera (despues de validar el body) ---------
    # Cuenta el intento por DNI aunque las credenciales fallen, para prevenir
    # fuerza bruta distribuida sin convertir el endpoint en un oracle de
    # existencia de usuarios.
    check_limit(
        request,
        LOGIN_IDENTITY_LIMIT,
        identity_key(KEY_PREFIX_LOGIN, credentials.dni),
        "login",
    )
    auth_service = AuthService(db)

    user = await auth_service.authenticate_user(credentials.dni, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = auth_service.create_token(user)
    return Token(access_token=access_token, user=UserResponse.model_validate(user))


@router.post("/login/staff", response_model=Token)
@limiter.limit("3/minute")
async def login_staff(
    request: Request,
    credentials: StaffLoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Token:
    """Staff login endpoint - authenticate a real staff user and return access token.

    Authenticates DNI + password against an existing, active User with role STAFF.
    No account is created and system_config.staff_password is not consulted for
    login. Any failure (unknown DNI, wrong password, inactive account, wrong role)
    answers with the same generic 401 so there is no credential oracle.
    Rate limit: 3 requests per minute to prevent brute force attacks.
    Identity limit: 5 requests per minute per normalized DNI.
    """
    # --- Check de identidad en frontera (despues de validar el body) ---------
    check_limit(
        request,
        LOGIN_IDENTITY_LIMIT,
        identity_key(KEY_PREFIX_LOGIN, credentials.dni),
        "login",
    )
    auth_service = AuthService(db)

    user = await auth_service.authenticate_staff(credentials.dni, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = auth_service.create_token(user)
    return Token(access_token=access_token, user=UserResponse.model_validate(user))


from app.schemas.security import AdminVerifyRequest, StaffPasswordUpdateRequest


@router.post("/verify-admin", status_code=status.HTTP_200_OK)
@limiter.limit("3/minute")
async def verify_admin(
    request: Request,
    credentials: AdminVerifyRequest,
    current_user: Annotated[User, Depends(require_role(["admin"]))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Verify admin password for sensitive operations.
    Requires authenticated admin user (JWT). Rate limit: 3 requests per minute."""
    from sqlalchemy import select

    from app.models.system_config import SystemConfig

    result = await db.execute(
        select(SystemConfig).where(SystemConfig.key == "admin_password")
    )
    config = result.scalar_one_or_none()

    stored = config.value if config else None

    if not stored:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin authentication is not configured",
        )

    if not _is_bcrypt_hash(stored):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Credenciales de admin en texto plano. Ejecutar "
                "backend/scripts/hash_config_passwords.py para convertir "
                "system_config a hash bcrypt antes de autenticar."
            ),
        )

    if not verify_password(credentials.password, stored):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
        )

    return {"message": "Admin verified"}


@router.post("/update-staff-password", status_code=status.HTTP_200_OK)
@limiter.limit("3/minute")
async def update_staff_password(
    request: Request,
    request_data: StaffPasswordUpdateRequest,
    current_user: Annotated[User, Depends(require_role(["admin"]))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update the password of a real staff user (requires admin JWT).

    El admin indica el DNI de un staff existente y activo y la nueva
    contraseña; se actualiza ese User. system_config.staff_password ya no se
    usa para el login (F2-05), por tanto este endpoint no toca esa clave de
    configuración. Rate limit: 3 requests per minute.
    """
    from sqlalchemy import select

    from app.models.user import User, UserRole

    result = await db.execute(select(User).where(User.dni == request_data.dni))
    user = result.scalar_one_or_none()

    if user is None or user.role != UserRole.STAFF or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario staff no encontrado",
        )

    user.hashed_password = get_password_hash(request_data.new_password)
    await db.commit()
    return {"message": "Contraseña de personal actualizada correctamente"}


@router.post(
    "/users/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
@limiter.limit("5/minute")
async def register(
    request: Request,
    user_data: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    """Register a new user."""
    # --- Check de identidad en frontera (despues de validar el body) ---------
    # El mismo DNI desde distintos clientes/IPs agota su propio contador;
    # identidades distintas no lo comparten.
    check_limit(
        request,
        REGISTER_IDENTITY_LIMIT,
        identity_key(KEY_PREFIX_REGISTER, user_data.dni),
        "register",
    )
    auth_service = AuthService(db)

    try:
        user = await auth_service.create_user(
            dni=user_data.dni,
            password=user_data.password,
            full_name=user_data.full_name,
        )
        return UserResponse.model_validate(user)
    except ValueError as e:
        # Handle DNI not authorized error
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario con este DNI",
        )
