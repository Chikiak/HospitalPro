from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole


class UserRepository:
    """Repository for User database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(
        self,
        dni: str,
        hashed_password: str,
        full_name: str,
        role: UserRole = UserRole.PATIENT,
        is_active: bool = True,
    ) -> User:
        """Create a new user."""
        user = User(
            dni=dni,
            hashed_password=hashed_password,
            full_name=full_name,
            role=role,
            is_active=is_active,
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
    
    async def get_by_dni(self, dni: str) -> Optional[User]:
        """Get user by DNI."""
        result = await self.session.execute(
            select(User).where(User.dni == dni)
        )
        return result.scalar_one_or_none()
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_all_patients(self) -> list[User]:
        """Get all patients."""
        result = await self.session.execute(
            select(User).where(User.role == UserRole.PATIENT).order_by(User.id)
        )
        return list(result.scalars().all())
