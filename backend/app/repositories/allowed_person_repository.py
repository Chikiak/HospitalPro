from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.allowed_person import AllowedPerson


class AllowedPersonRepository:
    """Repository for AllowedPerson database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def is_dni_allowed(self, dni: str) -> bool:
        """
        Check if a DNI is in the whitelist.
        
        Args:
            dni: The DNI to check
            
        Returns:
            True if the DNI is allowed, False otherwise
        """
        result = await self.session.execute(
            select(AllowedPerson).where(AllowedPerson.dni == dni)
        )
        allowed_person = result.scalar_one_or_none()
        return allowed_person is not None
    
    async def mark_as_registered(self, dni: str) -> None:
        """
        Mark a DNI as registered.
        
        Args:
            dni: The DNI to mark as registered
        """
        result = await self.session.execute(
            select(AllowedPerson).where(AllowedPerson.dni == dni)
        )
        allowed_person = result.scalar_one_or_none()
        if allowed_person:
            allowed_person.is_registered = True
            await self.session.commit()
    
    async def bulk_create(self, persons: list[dict]) -> list[AllowedPerson]:
        """
        Create multiple allowed persons at once.
        
        Args:
            persons: List of dicts with 'dni' and optional 'full_name' keys
            
        Returns:
            List of created AllowedPerson objects
        """
        allowed_persons = [
            AllowedPerson(
                dni=person["dni"],
                full_name=person.get("full_name"),
                is_registered=False
            )
            for person in persons
        ]
        self.session.add_all(allowed_persons)
        await self.session.commit()
        for person in allowed_persons:
            await self.session.refresh(person)
        return allowed_persons
    
    async def get_by_dni(self, dni: str) -> Optional[AllowedPerson]:
        """
        Get an allowed person by DNI.
        
        Args:
            dni: The DNI to look up
            
        Returns:
            The AllowedPerson object if found, None otherwise
        """
        result = await self.session.execute(
            select(AllowedPerson).where(AllowedPerson.dni == dni)
        )
        return result.scalar_one_or_none()
