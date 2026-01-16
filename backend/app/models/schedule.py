import enum
from datetime import time

from sqlalchemy import ForeignKey, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class DayOfWeek(int, enum.Enum):
    """Day of week enumeration (0=Monday, 6=Sunday)."""
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


class DoctorAvailability(Base):
    """Doctor availability model - defines when doctors are available."""
    __tablename__ = "doctor_availability"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    doctor_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    day_of_week: Mapped[DayOfWeek] = mapped_column(Integer, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    specialty: Mapped[str] = mapped_column(String(100), nullable=True)
    
    # Relationship to User model (doctor)
    # Note: We don't define the back_populates here to avoid modifying the existing User model
