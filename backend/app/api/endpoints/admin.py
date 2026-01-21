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
from app.schemas.security import AdminCategoryRequest

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
    # Verify admin password
    from app.api.endpoints.auth import verify_admin
    from app.schemas.security import AdminVerifyRequest
    await verify_admin(AdminVerifyRequest(password=schedule_data.admin_password), db)

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
        existing_schedule.start_date = schedule_data.start_date
        
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
            start_date=schedule_data.start_date,
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


@router.post("/categories", status_code=status.HTTP_201_CREATED)
async def create_category(
    request: AdminCategoryRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new category (specialty or lab) with a default schedule."""
    # 1. Verify admin password
    from app.api.endpoints.auth import verify_admin
    from app.schemas.security import AdminVerifyRequest
    await verify_admin(AdminVerifyRequest(password=request.admin_password), db)
    
    # 2. Create default schedule (e.g., Monday 08:00)
    from app.models.category_schedule import CategorySchedule, RotationType
    from datetime import time
    
    new_schedule = CategorySchedule(
        category_type=request.category_type,
        name=request.name,
        day_of_week=0, # Monday by default
        start_time=time(8, 0),
        turn_duration=30,
        max_turns_per_block=8,
        rotation_type=RotationType.FIXED,
        rotation_weeks=1
    )
    
    db.add(new_schedule)
    await db.commit()
    return {"message": f"Category {request.name} created successfully"}


@router.delete("/categories/{name}", status_code=status.HTTP_200_OK)
async def delete_category(
    name: str,
    admin_password: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete all schedules related to a category name."""
    # 1. Verify admin password
    from app.api.endpoints.auth import verify_admin
    from app.schemas.security import AdminVerifyRequest
    await verify_admin(AdminVerifyRequest(password=admin_password), db)
    
    # 2. Delete all schedules with that name
    from sqlalchemy import delete
    from app.models.category_schedule import CategorySchedule
    
    await db.execute(delete(CategorySchedule).where(CategorySchedule.name == name))
    await db.commit()
    return {"message": f"Category {name} and its schedules deleted successfully"}
