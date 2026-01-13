"""Data Transfer Objects for legacy Oracle database integration."""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class PatientHistory(BaseModel):
    """Patient history data from legacy Oracle database.
    
    This model includes validators to sanitize messy legacy data,
    particularly trimming whitespace from string fields.
    """
    dni: str = Field(..., description="Patient DNI/identification number")
    full_name: str = Field(..., description="Patient full name")
    birth_date: Optional[datetime] = Field(None, description="Patient birth date")
    blood_type: Optional[str] = Field(None, description="Blood type")
    allergies: Optional[List[str]] = Field(default_factory=list, description="List of allergies")
    medications: Optional[List[str]] = Field(default_factory=list, description="Current medications")
    medical_history: Optional[str] = Field(None, description="Medical history notes")
    last_visit: Optional[datetime] = Field(None, description="Last visit date")
    
    @field_validator('dni', 'full_name', 'blood_type', 'medical_history')
    @classmethod
    def strip_whitespace(cls, v: Optional[str]) -> Optional[str]:
        """Strip leading and trailing whitespace from string fields."""
        if v is not None and isinstance(v, str):
            return v.strip()
        return v
    
    @field_validator('allergies', 'medications')
    @classmethod
    def strip_list_items(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Strip whitespace from items in list fields."""
        if v is not None:
            return [item.strip() if isinstance(item, str) else item for item in v]
        return v
