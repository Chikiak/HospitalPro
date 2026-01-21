from pydantic import BaseModel, Field
from app.models.category_schedule import CategoryType


class AdminVerifyRequest(BaseModel):
    """Schema for admin password verification."""
    password: str = Field(..., min_length=1, description="Admin password")


class StaffPasswordUpdateRequest(BaseModel):
    """Schema for updating the staff password."""
    admin_password: str = Field(..., min_length=1, description="Admin password for authorization")
    new_staff_password: str = Field(..., min_length=1, description="New staff password")


class AdminCategoryRequest(BaseModel):
    """Schema for creating or updating a category (specialties/labs)."""
    admin_password: str = Field(..., min_length=1, description="Admin password for authorization")
    category_type: CategoryType
    name: str = Field(..., max_length=100)
    # This will create a DEFAULT schedule for the new name
