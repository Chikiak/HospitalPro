from pydantic import BaseModel, Field, field_validator
from app.models.category_schedule import CategoryType


class AdminVerifyRequest(BaseModel):
    """Schema for admin password verification."""
    password: str = Field(..., min_length=8, description="Admin password")


class StaffPasswordUpdateRequest(BaseModel):
    """Schema para actualizar la contraseña de un usuario staff real (F2-05).

    El admin indica el DNI de un staff existente y activo y la nueva
    contraseña; se actualiza ese User (system_config.staff_password ya no se
    usa para el login tras F2-05).
    """
    dni: str = Field(..., min_length=11, max_length=11, pattern=r"^\d{11}$", description="DNI del staff")
    new_password: str = Field(..., min_length=8, description="Nueva contraseña")


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
