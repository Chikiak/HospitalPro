import pytest
from datetime import datetime, time, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.models.schedule import DoctorAvailability, DayOfWeek
from app.models.appointment import Appointment, AppointmentStatus


@pytest.mark.asyncio
async def test_get_available_appointments_no_doctors(client: AsyncClient):
    """Test getting available appointments when no doctors exist for specialty."""
    response = await client.get("/appointments/available?specialty=Cardiology")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


@pytest.mark.asyncio
async def test_get_available_appointments_with_availability(client: AsyncClient, test_db: AsyncSession):
    """Test getting available appointments with doctor availability."""
    # Create a doctor user
    doctor = User(
        dni="DOC123",
        hashed_password="hashed",
        full_name="Dr. John Smith",
        role=UserRole.DOCTOR,
        is_active=True,
    )
    test_db.add(doctor)
    await test_db.commit()
    await test_db.refresh(doctor)
    
    # Create availability for the doctor (Monday, 9 AM)
    today = datetime.now()
    # Calculate next Monday
    days_ahead = 0 - today.weekday()  # 0 = Monday
    if days_ahead <= 0:
        days_ahead += 7
    next_monday = today + timedelta(days=days_ahead)
    
    availability = DoctorAvailability(
        doctor_id=doctor.id,
        day_of_week=DayOfWeek.MONDAY,
        start_time=time(9, 0),
        end_time=time(17, 0),
        specialty="Cardiology",
    )
    test_db.add(availability)
    await test_db.commit()
    
    # Get available appointments
    response = await client.get("/appointments/available?specialty=Cardiology")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    # Should return at most 3 slots
    assert len(data) <= 3
    
    # Verify the structure of the first slot
    first_slot = data[0]
    assert "doctor_id" in first_slot
    assert "doctor_name" in first_slot
    assert "specialty" in first_slot
    assert "appointment_date" in first_slot
    assert "available" in first_slot
    assert first_slot["doctor_id"] == doctor.id
    assert first_slot["doctor_name"] == doctor.full_name
    assert first_slot["specialty"] == "Cardiology"


@pytest.mark.asyncio
async def test_get_available_appointments_excludes_booked_slots(
    client: AsyncClient, test_db: AsyncSession
):
    """Test that booked slots are excluded from available appointments."""
    # Create a doctor user
    doctor = User(
        dni="DOC456",
        hashed_password="hashed",
        full_name="Dr. Jane Doe",
        role=UserRole.DOCTOR,
        is_active=True,
    )
    test_db.add(doctor)
    
    # Create a patient user
    patient = User(
        dni="PAT123",
        hashed_password="hashed",
        full_name="John Patient",
        role=UserRole.PATIENT,
        is_active=True,
    )
    test_db.add(patient)
    await test_db.commit()
    await test_db.refresh(doctor)
    await test_db.refresh(patient)
    
    # Create availability for the doctor (Tuesday, 10 AM)
    today = datetime.now()
    days_ahead = 1 - today.weekday()  # 1 = Tuesday
    if days_ahead <= 0:
        days_ahead += 7
    next_tuesday = today + timedelta(days=days_ahead)
    slot_time = datetime.combine(next_tuesday.date(), time(10, 0))
    
    availability = DoctorAvailability(
        doctor_id=doctor.id,
        day_of_week=DayOfWeek.TUESDAY,
        start_time=time(10, 0),
        end_time=time(18, 0),
        specialty="Dermatology",
    )
    test_db.add(availability)
    
    # Book an appointment for this exact slot
    appointment = Appointment(
        patient_id=patient.id,
        doctor_id=doctor.id,
        appointment_date=slot_time,
        status=AppointmentStatus.SCHEDULED,
        specialty="Dermatology",
    )
    test_db.add(appointment)
    await test_db.commit()
    
    # Get available appointments
    response = await client.get("/appointments/available?specialty=Dermatology")
    
    assert response.status_code == 200
    data = response.json()
    
    # The booked slot should not appear in available slots
    for slot in data:
        slot_datetime = datetime.fromisoformat(slot["appointment_date"].replace("Z", "+00:00"))
        # The slot_time should not be in the available slots
        assert slot_datetime != slot_time


@pytest.mark.asyncio
async def test_book_appointment_success(client: AsyncClient, test_db: AsyncSession):
    """Test successfully booking an appointment."""
    # Create a doctor user
    doctor = User(
        dni="DOC789",
        hashed_password="hashed",
        full_name="Dr. Bob Wilson",
        role=UserRole.DOCTOR,
        is_active=True,
    )
    test_db.add(doctor)
    await test_db.commit()
    await test_db.refresh(doctor)
    
    # Create appointment datetime (future date)
    appointment_date = datetime.now() + timedelta(days=7, hours=2)
    
    # Book the appointment
    response = await client.post(
        "/appointments/book",
        json={
            "doctor_id": doctor.id,
            "appointment_date": appointment_date.isoformat(),
            "specialty": "General Medicine",
            "notes": "First visit",
        },
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["doctor_id"] == doctor.id
    assert data["specialty"] == "General Medicine"
    assert data["notes"] == "First visit"
    assert data["status"] == "scheduled"
    assert "id" in data
    assert "patient_id" in data


@pytest.mark.asyncio
async def test_book_appointment_doctor_not_found(client: AsyncClient):
    """Test booking appointment with non-existent doctor."""
    appointment_date = datetime.now() + timedelta(days=7)
    
    response = await client.post(
        "/appointments/book",
        json={
            "doctor_id": 99999,  # Non-existent doctor
            "appointment_date": appointment_date.isoformat(),
            "specialty": "Cardiology",
        },
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_book_appointment_slot_already_taken(client: AsyncClient, test_db: AsyncSession):
    """Test booking an appointment when the slot is already taken."""
    # Create a doctor user
    doctor = User(
        dni="DOC999",
        hashed_password="hashed",
        full_name="Dr. Alice Brown",
        role=UserRole.DOCTOR,
        is_active=True,
    )
    test_db.add(doctor)
    
    # Create a patient user
    patient = User(
        dni="PAT999",
        hashed_password="hashed",
        full_name="Jane Patient",
        role=UserRole.PATIENT,
        is_active=True,
    )
    test_db.add(patient)
    await test_db.commit()
    await test_db.refresh(doctor)
    await test_db.refresh(patient)
    
    # Create an appointment datetime
    appointment_date = datetime.now() + timedelta(days=10)
    
    # Create an existing appointment
    existing_appointment = Appointment(
        patient_id=patient.id,
        doctor_id=doctor.id,
        appointment_date=appointment_date,
        status=AppointmentStatus.SCHEDULED,
        specialty="Orthopedics",
    )
    test_db.add(existing_appointment)
    await test_db.commit()
    
    # Try to book the same slot
    response = await client.post(
        "/appointments/book",
        json={
            "doctor_id": doctor.id,
            "appointment_date": appointment_date.isoformat(),
            "specialty": "Orthopedics",
        },
    )
    
    assert response.status_code == 409
    assert "no longer available" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_book_appointment_inactive_doctor(client: AsyncClient, test_db: AsyncSession):
    """Test booking appointment with inactive doctor."""
    # Create an inactive doctor user
    doctor = User(
        dni="DOC111",
        hashed_password="hashed",
        full_name="Dr. Inactive",
        role=UserRole.DOCTOR,
        is_active=False,  # Inactive
    )
    test_db.add(doctor)
    await test_db.commit()
    await test_db.refresh(doctor)
    
    appointment_date = datetime.now() + timedelta(days=7)
    
    response = await client.post(
        "/appointments/book",
        json={
            "doctor_id": doctor.id,
            "appointment_date": appointment_date.isoformat(),
            "specialty": "Neurology",
        },
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
