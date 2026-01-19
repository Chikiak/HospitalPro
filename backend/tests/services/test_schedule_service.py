import pytest
from datetime import datetime, time, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category_schedule import CategorySchedule, CategoryType, RotationType
from app.models.appointment import Appointment, AppointmentStatus
from app.models.user import User, UserRole
from app.services.schedule_service import ScheduleService


@pytest.mark.asyncio
async def test_get_available_slots_fixed_rotation(test_db: AsyncSession):
    """Test getting available slots for a FIXED rotation schedule."""
    # Create a category schedule with FIXED rotation
    category = CategorySchedule(
        category_type=CategoryType.SPECIALTY,
        name="Cardiology",
        day_of_week=0,  # Monday
        start_time=time(9, 0),
        turn_duration=30,
        max_turns_per_block=4,
        rotation_type=RotationType.FIXED,
        rotation_weeks=1,
    )
    test_db.add(category)
    await test_db.commit()
    await test_db.refresh(category)
    
    # Create service
    service = ScheduleService(test_db)
    
    # Test for a Monday
    test_date = datetime(2024, 1, 8, 0, 0)  # Monday, Jan 8, 2024
    slots = await service.get_available_slots(category.id, test_date)
    
    # Should have 4 slots (max_turns_per_block)
    assert len(slots) == 4
    
    # Check slot times
    assert slots[0].slot_datetime == datetime(2024, 1, 8, 9, 0)
    assert slots[1].slot_datetime == datetime(2024, 1, 8, 9, 30)
    assert slots[2].slot_datetime == datetime(2024, 1, 8, 10, 0)
    assert slots[3].slot_datetime == datetime(2024, 1, 8, 10, 30)
    
    # Check slot metadata
    assert all(slot.category_name == "Cardiology" for slot in slots)
    assert all(slot.category_id == category.id for slot in slots)


@pytest.mark.asyncio
async def test_get_available_slots_wrong_day(test_db: AsyncSession):
    """Test that no slots are returned for wrong day of week."""
    # Create a category schedule for Monday
    category = CategorySchedule(
        category_type=CategoryType.SPECIALTY,
        name="Cardiology",
        day_of_week=0,  # Monday
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
    
    # Test for a Tuesday (wrong day)
    test_date = datetime(2024, 1, 9, 0, 0)  # Tuesday
    slots = await service.get_available_slots(category.id, test_date)
    
    # Should have no slots
    assert len(slots) == 0


@pytest.mark.asyncio
async def test_get_available_slots_alternated_rotation_active_week(test_db: AsyncSession):
    """Test getting slots for ALTERNATED rotation on an active week."""
    # Create a category schedule with ALTERNATED rotation (every 2 weeks)
    category = CategorySchedule(
        category_type=CategoryType.LABORATORY,
        name="Blood Test",
        day_of_week=0,  # Monday
        start_time=time(8, 0),
        turn_duration=15,
        max_turns_per_block=3,
        rotation_type=RotationType.ALTERNATED,
        rotation_weeks=2,
    )
    test_db.add(category)
    await test_db.commit()
    await test_db.refresh(category)
    
    service = ScheduleService(test_db)
    
    # Test for Monday, Jan 1, 2024 (anchor date, week 0)
    test_date = datetime(2024, 1, 1, 0, 0)
    slots = await service.get_available_slots(category.id, test_date)
    
    # Should have 3 slots
    assert len(slots) == 3
    assert slots[0].slot_datetime == datetime(2024, 1, 1, 8, 0)
    assert slots[1].slot_datetime == datetime(2024, 1, 1, 8, 15)
    assert slots[2].slot_datetime == datetime(2024, 1, 1, 8, 30)


@pytest.mark.asyncio
async def test_get_available_slots_alternated_rotation_inactive_week(test_db: AsyncSession):
    """Test that no slots are returned for ALTERNATED rotation on an inactive week."""
    # Create a category schedule with ALTERNATED rotation (every 2 weeks)
    category = CategorySchedule(
        category_type=CategoryType.LABORATORY,
        name="Blood Test",
        day_of_week=0,  # Monday
        start_time=time(8, 0),
        turn_duration=15,
        max_turns_per_block=3,
        rotation_type=RotationType.ALTERNATED,
        rotation_weeks=2,
    )
    test_db.add(category)
    await test_db.commit()
    await test_db.refresh(category)
    
    service = ScheduleService(test_db)
    
    # Test for Monday, Jan 8, 2024 (week 1 from anchor, should be inactive)
    test_date = datetime(2024, 1, 8, 0, 0)
    slots = await service.get_available_slots(category.id, test_date)
    
    # Should have no slots (inactive week)
    assert len(slots) == 0


@pytest.mark.asyncio
async def test_get_available_slots_alternated_rotation_next_active_week(test_db: AsyncSession):
    """Test getting slots for ALTERNATED rotation on the next active week."""
    # Create a category schedule with ALTERNATED rotation (every 2 weeks)
    category = CategorySchedule(
        category_type=CategoryType.LABORATORY,
        name="Blood Test",
        day_of_week=0,  # Monday
        start_time=time(8, 0),
        turn_duration=15,
        max_turns_per_block=3,
        rotation_type=RotationType.ALTERNATED,
        rotation_weeks=2,
    )
    test_db.add(category)
    await test_db.commit()
    await test_db.refresh(category)
    
    service = ScheduleService(test_db)
    
    # Test for Monday, Jan 15, 2024 (week 2 from anchor, should be active again)
    test_date = datetime(2024, 1, 15, 0, 0)
    slots = await service.get_available_slots(category.id, test_date)
    
    # Should have 3 slots
    assert len(slots) == 3


@pytest.mark.asyncio
async def test_get_available_slots_filters_occupied(test_db: AsyncSession):
    """Test that occupied slots are filtered out."""
    # Create users (patient and doctor)
    patient = User(
        dni="12345678",
        hashed_password="hashed",
        full_name="John Doe",
        role=UserRole.PATIENT,
        is_active=True,
    )
    doctor = User(
        dni="87654321",
        hashed_password="hashed",
        full_name="Dr. Smith",
        role=UserRole.DOCTOR,
        is_active=True,
    )
    test_db.add(patient)
    test_db.add(doctor)
    await test_db.commit()
    await test_db.refresh(patient)
    await test_db.refresh(doctor)
    
    # Create a category schedule
    category = CategorySchedule(
        category_type=CategoryType.SPECIALTY,
        name="Cardiology",
        day_of_week=0,  # Monday
        start_time=time(9, 0),
        turn_duration=30,
        max_turns_per_block=4,
        rotation_type=RotationType.FIXED,
        rotation_weeks=1,
    )
    test_db.add(category)
    await test_db.commit()
    await test_db.refresh(category)
    
    # Create an appointment occupying the second slot (9:30)
    appointment = Appointment(
        patient_id=patient.id,
        doctor_id=doctor.id,
        appointment_date=datetime(2024, 1, 8, 9, 30),
        specialty="Cardiology",
        status=AppointmentStatus.SCHEDULED,
    )
    test_db.add(appointment)
    await test_db.commit()
    
    service = ScheduleService(test_db)
    
    # Test for Monday, Jan 8, 2024
    test_date = datetime(2024, 1, 8, 0, 0)
    slots = await service.get_available_slots(category.id, test_date)
    
    # Should have 3 slots (4 total - 1 occupied)
    assert len(slots) == 3
    
    # Verify the occupied slot (9:30) is not in the results
    slot_times = [slot.slot_datetime for slot in slots]
    assert datetime(2024, 1, 8, 9, 0) in slot_times
    assert datetime(2024, 1, 8, 9, 30) not in slot_times  # Occupied
    assert datetime(2024, 1, 8, 10, 0) in slot_times
    assert datetime(2024, 1, 8, 10, 30) in slot_times


@pytest.mark.asyncio
async def test_get_available_slots_filters_confirmed_appointments(test_db: AsyncSession):
    """Test that confirmed appointments are also filtered out."""
    # Create users
    patient = User(
        dni="12345678",
        hashed_password="hashed",
        full_name="John Doe",
        role=UserRole.PATIENT,
        is_active=True,
    )
    doctor = User(
        dni="87654321",
        hashed_password="hashed",
        full_name="Dr. Smith",
        role=UserRole.DOCTOR,
        is_active=True,
    )
    test_db.add(patient)
    test_db.add(doctor)
    await test_db.commit()
    await test_db.refresh(patient)
    await test_db.refresh(doctor)
    
    # Create a category schedule
    category = CategorySchedule(
        category_type=CategoryType.SPECIALTY,
        name="Cardiology",
        day_of_week=0,  # Monday
        start_time=time(9, 0),
        turn_duration=30,
        max_turns_per_block=4,
        rotation_type=RotationType.FIXED,
        rotation_weeks=1,
    )
    test_db.add(category)
    await test_db.commit()
    await test_db.refresh(category)
    
    # Create a confirmed appointment
    appointment = Appointment(
        patient_id=patient.id,
        doctor_id=doctor.id,
        appointment_date=datetime(2024, 1, 8, 9, 0),
        specialty="Cardiology",
        status=AppointmentStatus.CONFIRMED,
    )
    test_db.add(appointment)
    await test_db.commit()
    
    service = ScheduleService(test_db)
    
    # Test for Monday, Jan 8, 2024
    test_date = datetime(2024, 1, 8, 0, 0)
    slots = await service.get_available_slots(category.id, test_date)
    
    # Should have 3 slots (4 total - 1 confirmed)
    assert len(slots) == 3
    
    # Verify the confirmed slot is not in the results
    slot_times = [slot.slot_datetime for slot in slots]
    assert datetime(2024, 1, 8, 9, 0) not in slot_times  # Confirmed


@pytest.mark.asyncio
async def test_get_available_slots_allows_cancelled_appointments(test_db: AsyncSession):
    """Test that cancelled appointments don't block slots."""
    # Create users
    patient = User(
        dni="12345678",
        hashed_password="hashed",
        full_name="John Doe",
        role=UserRole.PATIENT,
        is_active=True,
    )
    doctor = User(
        dni="87654321",
        hashed_password="hashed",
        full_name="Dr. Smith",
        role=UserRole.DOCTOR,
        is_active=True,
    )
    test_db.add(patient)
    test_db.add(doctor)
    await test_db.commit()
    await test_db.refresh(patient)
    await test_db.refresh(doctor)
    
    # Create a category schedule
    category = CategorySchedule(
        category_type=CategoryType.SPECIALTY,
        name="Cardiology",
        day_of_week=0,  # Monday
        start_time=time(9, 0),
        turn_duration=30,
        max_turns_per_block=4,
        rotation_type=RotationType.FIXED,
        rotation_weeks=1,
    )
    test_db.add(category)
    await test_db.commit()
    await test_db.refresh(category)
    
    # Create a cancelled appointment
    appointment = Appointment(
        patient_id=patient.id,
        doctor_id=doctor.id,
        appointment_date=datetime(2024, 1, 8, 9, 0),
        specialty="Cardiology",
        status=AppointmentStatus.CANCELLED,
    )
    test_db.add(appointment)
    await test_db.commit()
    
    service = ScheduleService(test_db)
    
    # Test for Monday, Jan 8, 2024
    test_date = datetime(2024, 1, 8, 0, 0)
    slots = await service.get_available_slots(category.id, test_date)
    
    # Should have all 4 slots (cancelled appointment doesn't block)
    assert len(slots) == 4


@pytest.mark.asyncio
async def test_get_available_slots_nonexistent_category(test_db: AsyncSession):
    """Test that empty list is returned for nonexistent category."""
    service = ScheduleService(test_db)
    
    # Test with a nonexistent category ID
    test_date = datetime(2024, 1, 8, 0, 0)
    slots = await service.get_available_slots(999, test_date)
    
    # Should return empty list
    assert len(slots) == 0


@pytest.mark.asyncio
async def test_alternated_rotation_3_week_cycle(test_db: AsyncSession):
    """Test ALTERNATED rotation with a 3-week cycle."""
    # Create a category schedule with 3-week rotation
    category = CategorySchedule(
        category_type=CategoryType.LABORATORY,
        name="X-Ray",
        day_of_week=0,  # Monday
        start_time=time(10, 0),
        turn_duration=20,
        max_turns_per_block=2,
        rotation_type=RotationType.ALTERNATED,
        rotation_weeks=3,
    )
    test_db.add(category)
    await test_db.commit()
    await test_db.refresh(category)
    
    service = ScheduleService(test_db)
    
    # Test week 0 (Jan 1, 2024) - should be active
    test_date = datetime(2024, 1, 1, 0, 0)
    slots = await service.get_available_slots(category.id, test_date)
    assert len(slots) == 2
    
    # Test week 1 (Jan 8, 2024) - should be inactive
    test_date = datetime(2024, 1, 8, 0, 0)
    slots = await service.get_available_slots(category.id, test_date)
    assert len(slots) == 0
    
    # Test week 2 (Jan 15, 2024) - should be inactive
    test_date = datetime(2024, 1, 15, 0, 0)
    slots = await service.get_available_slots(category.id, test_date)
    assert len(slots) == 0
    
    # Test week 3 (Jan 22, 2024) - should be active again
    test_date = datetime(2024, 1, 22, 0, 0)
    slots = await service.get_available_slots(category.id, test_date)
    assert len(slots) == 2
