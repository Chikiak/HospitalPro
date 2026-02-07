from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AllowedPerson(Base):
    """
    Whitelist of DNIs authorized to register in the system.
    
    This model tracks which DNIs are allowed to create accounts and whether
    they have already registered.
    """
    __tablename__ = "allowed_persons"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    dni: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_registered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
