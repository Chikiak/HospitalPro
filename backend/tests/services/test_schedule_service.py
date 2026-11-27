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


@pytest.mark.asyncio
async def test_is_bookable_slot_fixed_active(test_db: AsyncSession):
    """is_bookable_slot devuelve True para un slot FIXED exacto y activo."""
    target = next_future_day()
    category = CategorySchedule(
        category_type=CategoryType.SPECIALTY,
        name="Cardiology",
        day_of_week=target.weekday(),
        start_time=time(9, 0),
        turn_duration=30,
        max_turns_per_block=4,
        rotation_type=RotationType.FIXED,
    )
    test_db.add(category)
    await test_db.commit()
    await test_db.refresh(category)

    service = ScheduleService(test_db)
    slot = datetime.combine(target.date(), time(9, 0))
    assert service.is_bookable_slot(category, slot) is True


@pytest.mark.asyncio
async def test_is_bookable_slot_rejects_non_exact_slot(test_db: AsyncSession):
    """Una hora que no cae en una franja exacta (start_time + k*turn_duration) no es reservable."""
    target = next_future_day()
    category = CategorySchedule(
        category_type=CategoryType.SPECIALTY,
        name="Cardiology",
        day_of_week=target.weekday(),
        start_time=time(9, 0),
        turn_duration=30,
        max_turns_per_block=4,
        rotation_type=RotationType.FIXED,
    )
    test_db.add(category)
    await test_db.commit()
    await test_db.refresh(category)

    service = ScheduleService(test_db)
    base = datetime.combine(target.date(), time(9, 0))
    assert service.is_bookable_slot(category, base.replace(minute=25)) is False  # no es múltiplo de 30 min
    assert service.is_bookable_slot(category, base.replace(hour=10, minute=5)) is False


@pytest.mark.asyncio
async def test_is_bookable_slot_rejects_wrong_weekday(test_db: AsyncSession):
    """Un día de la semana distinto al configurado no es reservable."""
    target = next_future_day()
    category = CategorySchedule(
        category_type=CategoryType.SPECIALTY,
        name="Cardiology",
        day_of_week=target.weekday(),
        start_time=time(9, 0),
        turn_duration=30,
        max_turns_per_block=4,
        rotation_type=RotationType.FIXED,
    )
    test_db.add(category)
    await test_db.commit()
    await test_db.refresh(category)

    service = ScheduleService(test_db)
    otro_dia = (target + timedelta(days=1)).replace(hour=9, minute=0)
    assert service.is_bookable_slot(category, otro_dia) is False


@pytest.mark.asyncio
async def test_is_bookable_slot_alternated_inactive_week(test_db: AsyncSession):
    """ALTERNATED rotation_weeks=2: semana 0 activa, semana 1 inactiva, semana 2 activa."""
    anchor = datetime(2024, 1, 1).date()  # lunes
    category = CategorySchedule(
        category_type=CategoryType.LABORATORY,
        name="Blood Test",
        day_of_week=0,
        start_time=time(8, 0),
        turn_duration=15,
        max_turns_per_block=3,
        rotation_type=RotationType.ALTERNATED,
        rotation_weeks=2,
        start_date=anchor,
    )
    test_db.add(category)
    await test_db.commit()
    await test_db.refresh(category)

    service = ScheduleService(test_db)
    assert service.is_bookable_slot(category, datetime(2024, 1, 1, 8, 0)) is True   # semana 0
    assert service.is_bookable_slot(category, datetime(2024, 1, 8, 8, 0)) is False  # semana 1 inactiva
    assert service.is_bookable_slot(category, datetime(2024, 1, 15, 8, 0)) is True  # semana 2


@pytest.mark.asyncio
async def test_is_bookable_slot_before_start_date(test_db: AsyncSession):
    """Una fecha anterior a start_date no es reservable aunque sea un weekday válido."""
    start_date = datetime(2024, 6, 1).date()
    category = CategorySchedule(
        category_type=CategoryType.LABORATORY,
        name="Blood Test",
        day_of_week=start_date.weekday(),
        start_time=time(8, 0),
        turn_duration=15,
        max_turns_per_block=3,
        rotation_type=RotationType.ALTERNATED,
        rotation_weeks=1,
        start_date=start_date,
    )
    test_db.add(category)
    await test_db.commit()
    await test_db.refresh(category)

    service = ScheduleService(test_db)
    assert service.is_bookable_slot(category, datetime(2024, 5, 1, 8, 0)) is False  # antes del inicio