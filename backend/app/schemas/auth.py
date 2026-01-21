from pydantic import BaseModel, Field
from app.schemas.user import UserResponse


class Token(BaseModel):
    """Schema for access token response."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class LoginRequest(BaseModel):
    """Schema for login request."""
    dni: str = Field(..., min_length=11, max_length=11, pattern=r"^\d{11}$", description="DNI/Cedula")
    password: str = Field(..., min_length=1, description="Password")


class StaffLoginRequest(BaseModel):
    """Schema for staff login request."""
    password: str = Field(..., min_length=1, description="Staff password")
