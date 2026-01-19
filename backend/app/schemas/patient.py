from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class PatientCreate(BaseModel):
    """Schema for creating a patient (step 1 of registration)."""
    dni: str = Field(..., min_length=11, max_length=11, pattern=r"^\d{11}$", description="DNI/Cedula")
    full_name: str = Field(..., min_length=1, max_length=255, description="Full name")
    password: str = Field(..., min_length=6, description="Password")


class TriageDataCreate(BaseModel):
    """Schema for creating triage data."""
    patient_id: int = Field(..., description="Patient user ID")
    medical_history: Optional[dict[str, Any]] = Field(None, description="Patient medical history as JSON object with flexible fields")
    allergies: Optional[str] = Field(None, description="Patient allergies")


class TriageDataUpdate(BaseModel):
    """Schema for updating triage data."""
    medical_history: Optional[dict[str, Any]] = Field(None, description="Patient medical history as JSON object with flexible fields")
    allergies: Optional[str] = Field(None, description="Patient allergies")


class TriageUpdate(BaseModel):
    """Schema for updating patient triage information (step 2 of registration)."""
    medical_history: Optional[dict[str, Any]] = Field(None, description="Patient medical history as JSON object with flexible fields")
    allergies: Optional[str] = Field(None, description="Patient allergies")


class TriageDataResponse(BaseModel):
    """Schema for triage data response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    patient_id: int
    medical_history: Optional[dict[str, Any]]
    allergies: Optional[str]
    last_updated: datetime
