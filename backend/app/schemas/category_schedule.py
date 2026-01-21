from datetime import time, date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.category_schedule import CategoryType, RotationType


class CategoryScheduleCreate(BaseModel):
    """Schema for creating a category schedule."""
    admin_password: str = Field(..., min_length=1, description="Admin password for authorization")
    category_type: CategoryType = Field(..., description="Type of category (specialty or laboratory)")
    name: str = Field(..., max_length=100, description="Name of the specialty or laboratory")
    day_of_week: int = Field(..., ge=0, le=6, description="Day of week (0=Monday, 6=Sunday)")
    start_time: time = Field(..., description="Start time of the availability block")
    turn_duration: int = Field(..., gt=0, description="Duration of each turn in minutes")
    max_turns_per_block: int = Field(..., gt=0, description="Maximum number of turns per block")
    rotation_type: RotationType = Field(..., description="Type of rotation (fixed or alternated)")
    rotation_weeks: int = Field(default=1, ge=1, description="Number of weeks in rotation cycle")
    start_date: Optional[date] = Field(None, description="Anchor date for rotation (Week A start)")


class CategoryScheduleUpdate(BaseModel):
    """Schema for updating a category schedule."""
    name: Optional[str] = Field(None, max_length=100, description="Name of the specialty or laboratory")
    start_time: Optional[time] = Field(None, description="Start time of the availability block")
    turn_duration: Optional[int] = Field(None, gt=0, description="Duration of each turn in minutes")
    max_turns_per_block: Optional[int] = Field(None, gt=0, description="Maximum number of turns per block")
    rotation_type: Optional[RotationType] = Field(None, description="Type of rotation (fixed or alternated)")
    rotation_weeks: Optional[int] = Field(None, ge=1, description="Number of weeks in rotation cycle")
    start_date: Optional[date] = Field(None, description="Anchor date for rotation (Week A start)")


class CategoryScheduleResponse(BaseModel):
    """Schema for category schedule response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    category_type: CategoryType
    name: str
    day_of_week: int
    start_time: time
    turn_duration: int
    max_turns_per_block: int
    rotation_type: RotationType
    rotation_weeks: int
    start_date: Optional[date] = None
