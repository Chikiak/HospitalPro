from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository


class AuthService:
    """Service for authentication operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
    
    async def authenticate_user(self, dni: str, password: str) -> Optional[User]:
        """Authenticate a user by DNI and password."""
        user = await self.user_repo.get_by_dni(dni)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        return user
    
    async def create_user(
        self,
        dni: str,
        password: str,
        full_name: str,
        role: UserRole = UserRole.PATIENT,
    ) -> User:
        """Create a new user with hashed password."""
        hashed_password = get_password_hash(password)
        user = await self.user_repo.create(
            dni=dni,
            hashed_password=hashed_password,
            full_name=full_name,
            role=role,
        )
        return user
    
    async def get_user_by_dni(self, dni: str) -> Optional[User]:
        """Get user by DNI."""
        return await self.user_repo.get_by_dni(dni)
    
    def create_token(self, user: User) -> str:
        """Create access token for user."""
        data = {"sub": user.dni, "role": user.role.value}
        return create_access_token(data)
