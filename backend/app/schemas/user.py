from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.user import UserRole


class UserCreate(BaseModel):
    """Schema for creating a user."""
    dni: str = Field(..., min_length=11, max_length=11, pattern=r"^\d{11}$", description="DNI/Cedula")
    password: str = Field(..., min_length=6, description="Password")
    full_name: str = Field(..., min_length=1, max_length=255, description="Full name")
    role: UserRole = Field(default=UserRole.PATIENT, description="User role")


class UserResponse(BaseModel):
    """Schema for user response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    dni: str
    full_name: str
    role: UserRole
    is_active: bool

    @field_validator("role", mode="before")
    @classmethod
    def normalize_role(cls, v):
        if isinstance(v, str):
            return v.lower()
        if hasattr(v, "value"):
            return v.value.lower()
        return v


class StaffLoginRequest(BaseModel):
    """Schema for staff login request."""
    password: str = Field(..., min_length=6, description="Password")
