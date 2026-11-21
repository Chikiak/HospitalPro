from datetime import datetime, time, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category_schedule import CategorySchedule, CategoryType, RotationType
from app.models.user import User, UserRole
from app.models.appointment import AppointmentStatus


@pytest.mark.asyncio
async def test_get_slots_by_category(client: AsyncClient, test_db: AsyncSession):
    """GET /appointments/slots con category_name y category_type: 200, <=3 slots, días distintos."""
    test_db.add(
        CategorySchedule(
            category_type=CategoryType.SPECIALTY,
            name="Cardiologia",
            day_of_week=0,
            start_time=time(9, 0),
            turn_duration=30,
            max_turns_per_block=2,
            rotation_type=RotationType.FIXED,
        )
    )
    await test_db.commit()

    response = await client.get(
        "/appointments/slots",
        params={"category_name": "Cardiologia", "category_type": "specialty"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 3
    days = {d["slot_datetime"][:10] for d in data}
    assert len(days) == len(data)


@pytest.mark.asyncio
async def test_book_appointment_with_token(client: AsyncClient, test_db: AsyncSession, make_token):
    """POST /appointments/book con token válido: 201 con specialty y status scheduled."""
    dni = "PACIENTE001"
    test_db.add(
        User(
            dni=dni,
            hashed_password="hashed",
            full_name="Paciente Prueba",
            role=UserRole.PATIENT,
            is_active=True,
        )
    )
    await test_db.commit()

    token = make_token(dni=dni, role="patient")
    appointment_date = datetime.now() + timedelta(days=7)

    response = await client.post(
        "/appointments/book",
        json={
            "category_id": 1,
            "appointment_date": appointment_date.isoformat(),
            "category_name": "Cardiologia",
            "notes": "Primera visita",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["specialty"] == "Cardiologia"
    assert data["status"] == "scheduled"
    assert data["patient_name"] == "Paciente Prueba"
    assert data["notes"] == "Primera visita"
    assert "id" in data


@pytest.mark.asyncio
async def test_book_appointment_without_token(client: AsyncClient):
    """POST /appointments/book sin token: 401."""
    response = await client.post(
        "/appointments/book",
        json={
            "category_id": 1,
            "appointment_date": (datetime.now() + timedelta(days=7)).isoformat(),
            "category_name": "Cardiologia",
        },
    )

    assert response.status_code == 401
