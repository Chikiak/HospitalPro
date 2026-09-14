import pytest
from datetime import datetime, time, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category_schedule import CategorySchedule, CategoryType, RotationType
from app.models.appointment import Appointment, AppointmentStatus
from app.models.user import User, UserRole
from app.services.schedule_service import ScheduleService


def next_future_day() -> datetime:
    """Return tomorrow at 00:00, guaranteed to be a future day the slot search will hit first."""
    return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)


@pytest.mark.asyncio
async def test_specialty_strict_daily_limit(test_db: AsyncSession):
    """Booking ANY slot in a specialty blocks the entire day (1 turn per day)."""
    target = next_future_day()
    category = CategorySchedule(
        category_type=CategoryType.SPECIALTY,
        name="Cardiologia_Strict",
        day_of_week=target.weekday(),
        start_time=time(8, 0),
        turn_duration=30,
        max_turns_per_block=2,
        rotation_type=RotationType.FIXED,
        rotation_weeks=1,
    )
    test_db.add(category)

    patient = User(dni="strict1", full_name="P", role=UserRole.PATIENT, hashed_password="x")
    test_db.add(patient)
    await test_db.commit()
    await test_db.refresh(patient)

    service = ScheduleService(test_db)
    booking_time = datetime.combine(target.date(), time(8, 0))

    # 1. Initially available
    slots = await service.get_next_available_slots("Cardiologia_Strict", CategoryType.SPECIALTY)
    assert len(slots) > 0
    assert slots[0].slot_datetime == booking_time

    # 2. Book the 8:00 slot
    appt = Appointment(
        patient_id=patient.id,
        appointment_date=booking_time,
        specialty="Cardiologia_Strict",
        status=AppointmentStatus.SCHEDULED,
    )
    test_db.add(appt)
    await test_db.commit()

    # 3. The whole day should now be GONE.
    slots_after = await service.get_next_available_slots("Cardiologia_Strict", CategoryType.SPECIALTY)
    if slots_after:
        assert slots_after[0].slot_datetime.date() != booking_time.date()


@pytest.mark.asyncio
async def test_laboratory_multiplex_capacity(test_db: AsyncSession):
    """Laboratories allow multiple bookings for the SAME time, up to max_turns_per_block."""
    target = next_future_day()
    category = CategorySchedule(
        category_type=CategoryType.LABORATORY,
        name="Laboratorio_Strict",
        day_of_week=target.weekday(),
        start_time=time(8, 0),
        turn_duration=30,
        max_turns_per_block=3,
        rotation_type=RotationType.FIXED,
        rotation_weeks=1,
    )
    test_db.add(category)

    patient = User(dni="strict2", full_name="P2", role=UserRole.PATIENT, hashed_password="x")
    test_db.add(patient)
    await test_db.commit()
    await test_db.refresh(patient)

    service = ScheduleService(test_db)
    booking_time = datetime.combine(target.date(), time(8, 0))

    # 1. Book one slot at 8:00 AM (1/3 taken) -> still available
    test_db.add(Appointment(
        patient_id=patient.id,
        appointment_date=booking_time,
        specialty="Laboratorio_Strict",
        status=AppointmentStatus.SCHEDULED,
    ))
    await test_db.commit()

    slots = await service.get_next_available_slots("Laboratorio_Strict", CategoryType.LABORATORY)
    assert len(slots) > 0
    assert slots[0].slot_datetime == booking_time

    # 2. Book 2 more (total 3) -> full capacity, day gone
    for _ in range(2):
        test_db.add(Appointment(
            patient_id=patient.id,
            appointment_date=booking_time,
            specialty="Laboratorio_Strict",
            status=AppointmentStatus.SCHEDULED,
        ))
    await test_db.commit()

    slots_full = await service.get_next_available_slots("Laboratorio_Strict", CategoryType.LABORATORY)
    if slots_full:
        assert slots_full[0].slot_datetime.date() != booking_time.date()