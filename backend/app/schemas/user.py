from pydantic import BaseModel, Field

from app.models.user import UserRole


class UserCreate(BaseModel):
    """Schema for creating a user."""
    dni: str = Field(..., min_length=1, max_length=20, description="DNI/Cedula")
    password: str = Field(..., min_length=6, description="Password")
    full_name: str = Field(..., min_length=1, max_length=255, description="Full name")
    role: UserRole = Field(default=UserRole.PATIENT, description="User role")


class UserResponse(BaseModel):
    """Schema for user response."""
    id: int
    dni: str
    full_name: str
    role: UserRole
    is_active: bool
    
    class Config:
        from_attributes = True
