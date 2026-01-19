import enum
from datetime import time

from sqlalchemy import Enum, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CategoryType(str, enum.Enum):
    """Category type enumeration."""
    SPECIALTY = "specialty"
    LABORATORY = "laboratory"


class RotationType(str, enum.Enum):
    """Rotation type enumeration."""
    FIXED = "fixed"
    ALTERNATED = "alternated"


class CategorySchedule(Base):
    """Category schedule model - defines when a category (Specialty or Laboratory) is available."""
    __tablename__ = "category_schedules"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    category_type: Mapped[CategoryType] = mapped_column(Enum(CategoryType), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    turn_duration: Mapped[int] = mapped_column(Integer, nullable=False)
    max_turns_per_block: Mapped[int] = mapped_column(Integer, nullable=False)
    rotation_type: Mapped[RotationType] = mapped_column(Enum(RotationType), nullable=False)
    rotation_weeks: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
