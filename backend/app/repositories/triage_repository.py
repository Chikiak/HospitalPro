from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patient import TriageData


class TriageRepository:
    """Repository for TriageData database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_patient_id(self, patient_id: int) -> Optional[TriageData]:
        """Get triage data by patient ID."""
        result = await self.session.execute(
            select(TriageData).where(TriageData.patient_id == patient_id)
        )
        return result.scalar_one_or_none()
    
    async def create(
        self,
        patient_id: int,
        medical_history: Optional[dict] = None,
        allergies: Optional[str] = None,
    ) -> TriageData:
        """Create new triage data for a patient."""
        triage_data = TriageData(
            patient_id=patient_id,
            medical_history=medical_history,
            allergies=allergies,
        )
        self.session.add(triage_data)
        await self.session.commit()
        await self.session.refresh(triage_data)
        return triage_data
    
    async def update(
        self,
        triage_data: TriageData,
        medical_history: Optional[dict] = None,
        allergies: Optional[str] = None,
    ) -> TriageData:
        """Update existing triage data."""
        if medical_history is not None:
            triage_data.medical_history = medical_history
        if allergies is not None:
            triage_data.allergies = allergies
        
        await self.session.commit()
        await self.session.refresh(triage_data)
        return triage_data
