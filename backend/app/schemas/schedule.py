from datetime import time
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.schedule import DayOfWeek


class DoctorAvailabilityCreate(BaseModel):
    """Schema for creating doctor availability."""
    doctor_id: int = Field(..., description="Doctor user ID")
    day_of_week: DayOfWeek = Field(..., description="Day of week (0=Monday, 6=Sunday)")
    start_time: time = Field(..., description="Start time")
    end_time: time = Field(..., description="End time")
    specialty: Optional[str] = Field(None, max_length=100, description="Medical specialty")


class DoctorAvailabilityUpdate(BaseModel):
    """Schema for updating doctor availability."""
    day_of_week: Optional[DayOfWeek] = Field(None, description="Day of week")
    start_time: Optional[time] = Field(None, description="Start time")
    end_time: Optional[time] = Field(None, description="End time")
    specialty: Optional[str] = Field(None, max_length=100, description="Medical specialty")


class DoctorAvailabilityResponse(BaseModel):
    """Schema for doctor availability response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    doctor_id: int
    day_of_week: DayOfWeek
    start_time: time
    end_time: time
    specialty: Optional[str]
