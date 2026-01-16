from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TriageDataCreate(BaseModel):
    """Schema for creating triage data."""
    patient_id: int = Field(..., description="Patient user ID")
    medical_history: Optional[str] = Field(None, description="Patient medical history")
    allergies: Optional[str] = Field(None, description="Patient allergies")


class TriageDataUpdate(BaseModel):
    """Schema for updating triage data."""
    medical_history: Optional[str] = Field(None, description="Patient medical history")
    allergies: Optional[str] = Field(None, description="Patient allergies")


class TriageDataResponse(BaseModel):
    """Schema for triage data response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    patient_id: int
    medical_history: Optional[str]
    allergies: Optional[str]
