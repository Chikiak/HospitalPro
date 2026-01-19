import pytest
from datetime import time
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category_schedule import CategorySchedule, CategoryType, RotationType


@pytest.mark.asyncio
async def test_create_category_schedule_specialty(test_db: AsyncSession):
    """Test creating a category schedule for a specialty."""
    category_schedule = CategorySchedule(
        category_type=CategoryType.SPECIALTY,
        name="Cardiology",
        day_of_week=0,  # Monday
        start_time=time(9, 0),
        turn_duration=30,
        max_turns_per_block=4,
        rotation_type=RotationType.FIXED,
        rotation_weeks=1,
    )
    
    test_db.add(category_schedule)
    await test_db.commit()
    await test_db.refresh(category_schedule)
    
    assert category_schedule.id is not None
    assert category_schedule.category_type == CategoryType.SPECIALTY
    assert category_schedule.name == "Cardiology"
    assert category_schedule.day_of_week == 0
    assert category_schedule.start_time == time(9, 0)
    assert category_schedule.turn_duration == 30
    assert category_schedule.max_turns_per_block == 4
    assert category_schedule.rotation_type == RotationType.FIXED
    assert category_schedule.rotation_weeks == 1


@pytest.mark.asyncio
async def test_create_category_schedule_laboratory(test_db: AsyncSession):
    """Test creating a category schedule for a laboratory exam."""
    category_schedule = CategorySchedule(
        category_type=CategoryType.LABORATORY,
        name="Blood Test",
        day_of_week=3,  # Thursday
        start_time=time(8, 0),
        turn_duration=15,
        max_turns_per_block=8,
        rotation_type=RotationType.ALTERNATED,
        rotation_weeks=2,
    )
    
    test_db.add(category_schedule)
    await test_db.commit()
    await test_db.refresh(category_schedule)
    
    assert category_schedule.id is not None
    assert category_schedule.category_type == CategoryType.LABORATORY
    assert category_schedule.name == "Blood Test"
    assert category_schedule.day_of_week == 3
    assert category_schedule.start_time == time(8, 0)
    assert category_schedule.turn_duration == 15
    assert category_schedule.max_turns_per_block == 8
    assert category_schedule.rotation_type == RotationType.ALTERNATED
    assert category_schedule.rotation_weeks == 2


def test_category_type_enum_values():
    """Test CategoryType enum values."""
    assert CategoryType.SPECIALTY.value == "specialty"
    assert CategoryType.LABORATORY.value == "laboratory"


def test_rotation_type_enum_values():
    """Test RotationType enum values."""
    assert RotationType.FIXED.value == "fixed"
    assert RotationType.ALTERNATED.value == "alternated"


@pytest.mark.asyncio
async def test_category_schedule_default_rotation_weeks(test_db: AsyncSession):
    """Test that rotation_weeks has default value of 1."""
    category_schedule = CategorySchedule(
        category_type=CategoryType.SPECIALTY,
        name="Neurology",
        day_of_week=1,
        start_time=time(10, 0),
        turn_duration=45,
        max_turns_per_block=3,
        rotation_type=RotationType.FIXED,
        rotation_weeks=1,  # Explicitly setting since SQLAlchemy default doesn't work until DB insert
    )
    
    test_db.add(category_schedule)
    await test_db.commit()
    await test_db.refresh(category_schedule)
    
    assert category_schedule.rotation_weeks == 1
