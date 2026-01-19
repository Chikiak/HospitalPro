from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TriageData(Base):
    """Triage data model - stores patient medical history and allergies.
    
    Note: medical_history is stored as JSON to support flexible fields for patient onboarding.
    The JSON structure can contain any relevant medical information as key-value pairs.
    """
    __tablename__ = "triage_data"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    medical_history: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    allergies: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_updated: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to User model
    # Note: We don't define the back_populates here to avoid modifying the existing User model
