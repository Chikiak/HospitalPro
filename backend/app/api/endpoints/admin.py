from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_role
from app.core.rate_limit import limiter
from app.models.category_schedule import CategorySchedule
from app.models.user import User
from app.schemas.category_schedule import (
    CategoryScheduleCreate,
    CategoryScheduleResponse,
)
from app.schemas.security import AdminCategoryRequest, AdminDniRequest

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post(
    "/schedules",
    response_model=CategoryScheduleResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("10/min")
async def create_or_update_schedule(
    request: Request,
    schedule_data: CategoryScheduleCreate,
    current_user: Annotated[User, Depends(require_role(["admin"]))],
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> CategoryScheduleResponse:
    """
    Create or update a category schedule block.

    Requires authenticated admin user (JWT). Rate limit: 10 requests per minute.

    This endpoint enforces a unique constraint: only one schedule block is allowed
    per combination of category name and day_of_week. This allows multiple
    specialties or laboratories to operate on the same day.

    If a schedule already exists for the given category name and day_of_week,
    it will be updated with the new data. Otherwise, a new schedule is created.

    Args:
        request: HTTP request (for rate limiting)
        schedule_data: The schedule data to create or update
        current_user: Authenticated admin user
        db: Database session

    Returns:
        The created or updated schedule
    """
    # Check if a schedule already exists for this category name and day_of_week
    existing_query = select(CategorySchedule).where(
        and_(
            CategorySchedule.name == schedule_data.name,
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
        existing_schedule.deadline_time = schedule_data.deadline_time
        existing_schedule.warning_message = schedule_data.warning_message

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
            deadline_time=schedule_data.deadline_time,
            warning_message=schedule_data.warning_message,
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

    Public endpoint (no authentication required).

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
@limiter.limit("10/min")
async def create_category(
    request: Request,
    request_data: AdminCategoryRequest,
    current_user: Annotated[User, Depends(require_role(["admin"]))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new category (specialty or lab) with a default schedule.
    Requires authenticated admin user (JWT). Rate limit: 10 requests per minute."""
    from app.models.category_schedule import CategorySchedule, RotationType
    from datetime import time

    new_schedule = CategorySchedule(
        category_type=request_data.category_type,
        name=request_data.name,
        day_of_week=0,  # Monday by default
        start_time=time(8, 0),
        turn_duration=30,
        max_turns_per_block=8,
        rotation_type=RotationType.FIXED,
        rotation_weeks=1,
    )

    db.add(new_schedule)
    await db.commit()
    return {"message": f"Category {request_data.name} created successfully"}


@router.delete("/categories/{name}", status_code=status.HTTP_200_OK)
@limiter.limit("10/min")
async def delete_category(
    request: Request,
    name: str,
    current_user: Annotated[User, Depends(require_role(["admin"]))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete all schedules related to a category name.
    Requires authenticated admin user (JWT). Rate limit: 10 requests per minute.
    No admin_password parameter required."""
    await db.execute(delete(CategorySchedule).where(CategorySchedule.name == name))
    await db.commit()
    return {"message": f"Category {name} and its schedules deleted successfully"}


@router.post("/allowed-persons", status_code=status.HTTP_201_CREATED)
@limiter.limit("10/min")
async def add_allowed_person(
    request: Request,
    request_data: AdminDniRequest,
    current_user: Annotated[User, Depends(require_role(["admin"]))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Add a DNI to the allowed registrations whitelist (admin).
    Requires authenticated admin user (JWT). Rate limit: 10 requests per minute."""
    from app.models.allowed_person import AllowedPerson
    from app.repositories.allowed_person_repository import AllowedPersonRepository

    repo = AllowedPersonRepository(db)

    # Check if already exists
    existing = await repo.get_by_dni(request_data.dni)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este DNI ya está en la lista de autorizados",
        )

    await repo.bulk_create([{"dni": request_data.dni, "full_name": request_data.full_name}])

    return {"message": f"DNI {request_data.dni} agregado correctamente"}
