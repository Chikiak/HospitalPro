from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SystemConfig(Base):
    """System configuration model for dynamic settings like passwords."""
    __tablename__ = "system_config"
    
    key: Mapped[str] = mapped_column(String(50), primary_key=True, index=True)
    value: Mapped[str] = mapped_column(String(255), nullable=False)
