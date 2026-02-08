from typing import Annotated
import secrets

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token
from app.core.rate_limit import limiter
from app.models.user import UserRole
from app.schemas.auth import LoginRequest, StaffLoginRequest, Token
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login/access-token", response_model=Token)
@limiter.limit("5/minute")
async def login(
    request: Request,
    credentials: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Token:
    """Login endpoint - authenticate user and return access token.
    
    Rate limit: 5 requests per minute to prevent brute force attacks.
    """
    auth_service = AuthService(db)
    
    user = await auth_service.authenticate_user(credentials.dni, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="DNI o contraseña incorrectos",
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
    """Staff login endpoint - authenticate staff and return access token with staff role.
    
    Rate limit: 3 requests per minute to prevent brute force attacks on admin accounts.
    """
    from sqlalchemy import select
    from app.models.system_config import SystemConfig
    from app.models.user import User
    
    # Try to get persistent staff password from database
    result = await db.execute(select(SystemConfig).where(SystemConfig.key == "staff_password"))
    config = result.scalar_one_or_none()
    
    current_staff_password = config.value if config else settings.STAFF_PASSWORD
    
    if not current_staff_password:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Staff authentication is not configured",
        )
    
    # Use constant-time comparison to prevent timing attacks
    if not secrets.compare_digest(credentials.password, current_staff_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Contraseña de staff incorrecta",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get or create a real staff user in the database
    result = await db.execute(select(User).where(User.dni == "staff"))
    staff_user = result.scalar_one_or_none()
    
    if not staff_user:
        # Create the staff user if it doesn't exist
        from app.core.security import get_password_hash
        staff_user = User(
            dni="staff",
            hashed_password=get_password_hash(current_staff_password),
            full_name="Personal Administrativo",
            role=UserRole.STAFF,
            is_active=True
        )
        db.add(staff_user)
        await db.commit()
        await db.refresh(staff_user)
    
    # Create token with staff role
    access_token = create_access_token({"sub": staff_user.dni, "role": UserRole.STAFF.value})
    
    return Token(access_token=access_token, user=UserResponse.model_validate(staff_user))


from app.schemas.security import AdminVerifyRequest, StaffPasswordUpdateRequest

@router.post("/verify-admin", status_code=status.HTTP_200_OK)
async def verify_admin(
    credentials: AdminVerifyRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Verify admin password for sensitive operations."""
    from sqlalchemy import select
    from app.models.system_config import SystemConfig
    
    # Try to get persistent admin password from database
    result = await db.execute(select(SystemConfig).where(SystemConfig.key == "admin_password"))
    config = result.scalar_one_or_none()
    
    current_admin_password = config.value if config else settings.ADMIN_PASSWORD
    
    if not secrets.compare_digest(credentials.password, current_admin_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Contraseña de administrador incorrecta",
        )
    
    return {"message": "Admin verified"}


@router.post("/update-staff-password", status_code=status.HTTP_200_OK)
async def update_staff_password(
    request: StaffPasswordUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update the staff password (requires admin authorization)."""
    # 1. Verify admin password
    await verify_admin(AdminVerifyRequest(password=request.admin_password), db)
    
    # 2. Update staff password in database
    from sqlalchemy import select
    from app.models.system_config import SystemConfig
    
    result = await db.execute(select(SystemConfig).where(SystemConfig.key == "staff_password"))
    config = result.scalar_one_or_none()
    
    if config:
        config.value = request.new_staff_password
    else:
        config = SystemConfig(key="staff_password", value=request.new_staff_password)
        db.add(config)
    
    await db.commit()
    return {"message": "Staff password updated successfully"}


@router.post("/users/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    """Register a new user."""
    auth_service = AuthService(db)
    
    try:
        user = await auth_service.create_user(
            dni=user_data.dni,
            password=user_data.password,
            full_name=user_data.full_name,
            role=user_data.role,
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
