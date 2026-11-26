from pydantic import BaseModel, Field, field_validator
from app.models.category_schedule import CategoryType


class AdminVerifyRequest(BaseModel):
    """Schema for admin password verification."""
    password: str = Field(..., min_length=8, description="Admin password")


class StaffPasswordUpdateRequest(BaseModel):
    """Schema for updating the staff password."""
    new_staff_password: str = Field(..., min_length=8, description="New staff password")


class AdminCategoryRequest(BaseModel):
    """Schema for creating or updating a category (specialties/labs)."""
    category_type: CategoryType
    name: str = Field(..., max_length=100)
    # This will create a DEFAULT schedule for the new name


class AdminDniRequest(BaseModel):
    """Schema for adding an allowed DNI."""
    dni: str = Field(..., min_length=11, max_length=11, pattern=r"^\d{11}$")
    full_name: str | None = Field(None, max_length=255)

    @field_validator("dni", mode="before")
    @classmethod
    def validate_dni_format(cls, v):
        """Valida que el DNI tenga exactamente 11 dígitos numéricos (mensaje en español).

        Se usa mode="before" para que esta validación se ejecute antes que las
        restricciones de Field y emita el mensaje en español en lugar del
        error por defecto de Pydantic (en inglés).
        """
        if not isinstance(v, str) or not v.isdigit() or len(v) != 11:
            raise ValueError("El DNI debe contener exactamente 11 dígitos numéricos")
        return v
