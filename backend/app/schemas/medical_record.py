from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class MedicalRecordEntryCreate(BaseModel):
    """Schema for creating a new medical record entry."""
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "entry_type": "consultation",
            "specialty": "Cardiology",
            "doctor_name": "Dr. Juan Pérez",
            "diagnosis": "Hypertension",
            "notes": "Patient advised to reduce salt intake"
        }
    })
    
    entry_type: str = Field(..., description="Type of entry: 'consultation' or 'lab_result'")
    specialty: Optional[str] = Field(None, description="Medical specialty")
    doctor_name: Optional[str] = Field(None, description="Name of the attending doctor")
    diagnosis: Optional[str] = Field(None, description="Diagnosis or findings")
    notes: Optional[str] = Field(None, description="Additional notes")
    results: Optional[dict[str, Any]] = Field(None, description="Lab results or other data")


class MedicalRecordResponse(BaseModel):
    """Schema for medical record response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    patient_id: int
    registration_survey: Optional[dict[str, Any]] = None
    entries: list[dict[str, Any]] = []
    created_at: datetime
    last_updated: datetime


class AllowedPersonCreate(BaseModel):
    """Schema for creating an allowed person."""
    
    dni: str = Field(..., description="DNI of the person")
    full_name: Optional[str] = Field(None, description="Full name of the person")


class AllowedPersonBulkCreate(BaseModel):
    """Schema for bulk creating allowed persons."""
    
    persons: list[AllowedPersonCreate] = Field(..., description="List of persons to add")
