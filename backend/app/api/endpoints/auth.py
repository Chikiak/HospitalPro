from typing import Annotated
import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token
from app.schemas.auth import LoginRequest, StaffLoginRequest, Token
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login/access-token", response_model=Token)
async def login(
    credentials: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Token:
    """Login endpoint - authenticate user and return access token."""
    auth_service = AuthService(db)
    
    user = await auth_service.authenticate_user(credentials.dni, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="DNI o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth_service.create_token(user)
    return Token(access_token=access_token)


@router.post("/login/staff", response_model=Token)
async def login_staff(
    credentials: StaffLoginRequest,
) -> Token:
    """Staff login endpoint - authenticate staff and return access token with staff role."""
    # Validate that STAFF_PASSWORD is configured
    if not settings.STAFF_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Staff authentication is not configured",
        )
    
    # Use constant-time comparison to prevent timing attacks
    if not secrets.compare_digest(credentials.password, settings.STAFF_PASSWORD):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Contraseña de staff incorrecta",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create token with staff role
    access_token = create_access_token({"sub": "staff", "role": "staff"})
    return Token(access_token=access_token)


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
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario con este DNI",
        )
