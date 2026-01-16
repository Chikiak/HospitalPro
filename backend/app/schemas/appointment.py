from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.appointment import AppointmentStatus


class AppointmentCreate(BaseModel):
    """Schema for creating an appointment."""
    patient_id: int = Field(..., description="Patient user ID")
    doctor_id: int = Field(..., description="Doctor user ID")
    appointment_date: datetime = Field(..., description="Appointment date and time")
    specialty: Optional[str] = Field(None, max_length=100, description="Medical specialty")
    notes: Optional[str] = Field(None, max_length=500, description="Appointment notes")


class AppointmentUpdate(BaseModel):
    """Schema for updating an appointment."""
    appointment_date: Optional[datetime] = Field(None, description="Appointment date and time")
    status: Optional[AppointmentStatus] = Field(None, description="Appointment status")
    notes: Optional[str] = Field(None, max_length=500, description="Appointment notes")


class AppointmentResponse(BaseModel):
    """Schema for appointment response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    patient_id: int
    doctor_id: int
    appointment_date: datetime
    status: AppointmentStatus
    specialty: Optional[str]
    notes: Optional[str]


class AvailableSlot(BaseModel):
    """Schema for available appointment slot."""
    doctor_id: int
    doctor_name: str
    specialty: str
    appointment_date: datetime
    available: bool = True


class BookAppointmentRequest(BaseModel):
    """Schema for booking an appointment."""
    doctor_id: int = Field(..., description="Doctor user ID")
    appointment_date: datetime = Field(..., description="Appointment date and time")
    specialty: str = Field(..., max_length=100, description="Medical specialty")
    notes: Optional[str] = Field(None, max_length=500, description="Appointment notes")
