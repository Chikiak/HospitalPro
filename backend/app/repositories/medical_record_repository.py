from datetime import datetime
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.medical_record import MedicalRecord


class MedicalRecordRepository:
    """Repository for MedicalRecord database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(
        self, 
        patient_id: int, 
        registration_survey: Optional[dict[str, Any]] = None
    ) -> MedicalRecord:
        """
        Create a new medical record for a patient.
        
        Args:
            patient_id: The patient's user ID
            registration_survey: Initial survey data from registration
            
        Returns:
            The created MedicalRecord object
        """
        medical_record = MedicalRecord(
            patient_id=patient_id,
            registration_survey=registration_survey,
            entries=[]
        )
        self.session.add(medical_record)
        await self.session.commit()
        await self.session.refresh(medical_record)
        return medical_record
    
    async def get_by_patient_id(self, patient_id: int) -> Optional[MedicalRecord]:
        """
        Get the medical record for a patient.
        
        Args:
            patient_id: The patient's user ID
            
        Returns:
            The MedicalRecord object if found, None otherwise
        """
        result = await self.session.execute(
            select(MedicalRecord).where(MedicalRecord.patient_id == patient_id)
        )
        return result.scalar_one_or_none()
    
    async def add_entry(self, patient_id: int, entry: dict[str, Any]) -> MedicalRecord:
        """
        Add a new entry (consultation or lab result) to a patient's medical record.
        
        Args:
            patient_id: The patient's user ID
            entry: The entry data to add
            
        Returns:
            The updated MedicalRecord object
        """
        result = await self.session.execute(
            select(MedicalRecord).where(MedicalRecord.patient_id == patient_id)
        )
        medical_record = result.scalar_one_or_none()
        
        if not medical_record:
            raise ValueError(f"No medical record found for patient {patient_id}")
        
        # Add timestamp to entry
        entry_with_timestamp = {
            **entry,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Append to entries array
        if medical_record.entries is None:
            medical_record.entries = []
        
        current_entries = medical_record.entries.copy() if medical_record.entries else []
        current_entries.append(entry_with_timestamp)
        medical_record.entries = current_entries
        
        await self.session.commit()
        await self.session.refresh(medical_record)
        return medical_record
