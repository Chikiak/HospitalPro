from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class MedicalRecord(Base):
    """
    Formal medical history for patients.
    
    This model stores the complete medical record for a patient, including
    the initial registration survey and all subsequent medical entries
    (consultations and laboratory results).
    """
    __tablename__ = "medical_records"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("users.id"), 
        unique=True, 
        index=True, 
        nullable=False
    )
    registration_survey: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    entries: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=True, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    last_updated: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
