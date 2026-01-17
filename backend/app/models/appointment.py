import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AppointmentStatus(str, enum.Enum):
    """Appointment status enumeration."""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class Appointment(Base):
    """Appointment model - manages patient appointments with doctors."""
    __tablename__ = "appointments"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    doctor_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    appointment_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(AppointmentStatus), 
        nullable=False, 
        default=AppointmentStatus.SCHEDULED
    )
    specialty: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Relationships to User model (patient and doctor)
    # Note: We don't define the back_populates here to avoid modifying the existing User model
