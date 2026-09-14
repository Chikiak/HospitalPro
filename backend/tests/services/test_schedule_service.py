import pytest
from datetime import datetime, time, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category_schedule import CategorySchedule, CategoryType, RotationType
from app.services.schedule_service import ScheduleService


def next_future_day() -> datetime:
    """Return tomorrow at 00:00, guaranteed to be a future day that the slot search will hit first."""
    return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)


@pytest.mark.asyncio
async def test_fixed_rotation_returns_three_distinct_days(test_db: AsyncSession):
    """A FIXED schedule should yield 3 suggestions on 3 DIFFERENT days."""
    target = next_future_day()
    category = CategorySchedule(
        category_type=CategoryType.SPECIALTY,
        name="Cardiology",
        day_of_week=target.weekday(),
        start_time=time(9, 0),
        turn_duration=30,
        max_turns_per_block=4,
        rotation_type=RotationType.FIXED,
        rotation_weeks=1,
    )
    test_db.add(category)
    await test_db.commit()
    await test_db.refresh(category)

    service = ScheduleService(test_db)
    slots = await service.get_next_available_slots("Cardiology", CategoryType.SPECIALTY, limit=3)

    assert len(slots) == 3
    dates = {s.slot_datetime.date() for s in slots}
    assert len(dates) == 3
    assert slots[0].slot_datetime == datetime.combine(target.date(), time(9, 0))
    assert all(s.category_name == "Cardiology" and s.category_id == category.id for s in slots)


@pytest.mark.asyncio
async def test_alternated_rotation_2_week_cycle(test_db: AsyncSession):
    """ALTERNATED (2-week) rotation: active on weeks 0 and 2, inactive on week 1."""
    category = CategorySchedule(
        category_type=CategoryType.LABORATORY,
        name="Blood Test",
        day_of_week=0,
        start_time=time(8, 0),
        turn_duration=15,
        max_turns_per_block=3,
        rotation_type=RotationType.ALTERNATED,
        rotation_weeks=2,
        start_date=datetime(2024, 1, 1).date(),
    )
    test_db.add(category)
    await test_db.commit()
    await test_db.refresh(category)

    service = ScheduleService(test_db)
    assert service._is_schedule_active(category, datetime(2024, 1, 1)) is True   # week 0
    assert service._is_schedule_active(category, datetime(2024, 1, 8)) is False   # week 1
    assert service._is_schedule_active(category, datetime(2024, 1, 15)) is True   # week 2


@pytest.mark.asyncio
async def test_alternated_rotation_3_week_cycle(test_db: AsyncSession):
    """ALTERNATED (3-week) rotation: active only on weeks 0 and 3."""
    category = CategorySchedule(
        category_type=CategoryType.LABORATORY,
        name="X-Ray",
        day_of_week=0,
        start_time=time(10, 0),
        turn_duration=20,
        max_turns_per_block=2,
        rotation_type=RotationType.ALTERNATED,
        rotation_weeks=3,
        start_date=datetime(2024, 1, 1).date(),
    )
    test_db.add(category)
    await test_db.commit()
    await test_db.refresh(category)

    service = ScheduleService(test_db)
    assert service._is_schedule_active(category, datetime(2024, 1, 1)) is True   # week 0
    assert service._is_schedule_active(category, datetime(2024, 1, 8)) is False   # week 1
    assert service._is_schedule_active(category, datetime(2024, 1, 15)) is False  # week 2
    assert service._is_schedule_active(category, datetime(2024, 1, 22)) is True   # week 3


@pytest.mark.asyncio
async def test_alternated_rotation_before_anchor(test_db: AsyncSession):
    """Dates before the anchor date should be inactive."""
    category = CategorySchedule(
        category_type=CategoryType.LABORATORY,
        name="Blood Test",
        day_of_week=0,
        start_time=time(8, 0),
        turn_duration=15,
        max_turns_per_block=3,
        rotation_type=RotationType.ALTERNATED,
        rotation_weeks=2,
        start_date=datetime(2024, 1, 1).date(),
    )
    test_db.add(category)
    await test_db.commit()
    await test_db.refresh(category)

    service = ScheduleService(test_db)
    assert service._is_schedule_active(category, datetime(2023, 12, 25)) is False