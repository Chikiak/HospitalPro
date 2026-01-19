from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.category_schedule import CategorySchedule
from app.schemas.category_schedule import (
    CategoryScheduleCreate,
    CategoryScheduleResponse,
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/schedules", response_model=CategoryScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_or_update_schedule(
    schedule_data: CategoryScheduleCreate,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> CategoryScheduleResponse:
    """
    Create or update a category schedule block.
    
    This endpoint enforces a unique constraint: only one schedule block is allowed
    per combination of category_type and day_of_week.
    
    If a schedule already exists for the given category_type and day_of_week,
    it will be updated with the new data. Otherwise, a new schedule is created.
    
    Args:
        schedule_data: The schedule data to create or update
        db: Database session
        
    Returns:
        The created or updated schedule
    """
    # Check if a schedule already exists for this category_type and day_of_week
    existing_query = select(CategorySchedule).where(
        and_(
            CategorySchedule.category_type == schedule_data.category_type,
            CategorySchedule.day_of_week == schedule_data.day_of_week
        )
    )
    result = await db.execute(existing_query)
    existing_schedule = result.scalar_one_or_none()
    
    if existing_schedule:
        # Update existing schedule
        existing_schedule.name = schedule_data.name
        existing_schedule.start_time = schedule_data.start_time
        existing_schedule.turn_duration = schedule_data.turn_duration
        existing_schedule.max_turns_per_block = schedule_data.max_turns_per_block
        existing_schedule.rotation_type = schedule_data.rotation_type
        existing_schedule.rotation_weeks = schedule_data.rotation_weeks
        
        await db.commit()
        await db.refresh(existing_schedule)
        
        return CategoryScheduleResponse.model_validate(existing_schedule)
    else:
        # Create new schedule
        new_schedule = CategorySchedule(
            category_type=schedule_data.category_type,
            name=schedule_data.name,
            day_of_week=schedule_data.day_of_week,
            start_time=schedule_data.start_time,
            turn_duration=schedule_data.turn_duration,
            max_turns_per_block=schedule_data.max_turns_per_block,
            rotation_type=schedule_data.rotation_type,
            rotation_weeks=schedule_data.rotation_weeks,
        )
        
        db.add(new_schedule)
        await db.commit()
        await db.refresh(new_schedule)
        
        return CategoryScheduleResponse.model_validate(new_schedule)


@router.get("/schedules", response_model=List[CategoryScheduleResponse])
async def list_schedules(
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> List[CategoryScheduleResponse]:
    """
    List all category schedule configurations.
    
    Returns all schedule blocks currently configured in the system,
    ordered by category_type and day_of_week for easy reading.
    
    Args:
        db: Database session
        
    Returns:
        List of all category schedules
    """
    query = select(CategorySchedule).order_by(
        CategorySchedule.category_type,
        CategorySchedule.day_of_week
    )
    result = await db.execute(query)
    schedules = result.scalars().all()
    
    return [CategoryScheduleResponse.model_validate(schedule) for schedule in schedules]
