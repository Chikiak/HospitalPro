from datetime import datetime, time, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.category_schedule import CategorySchedule, CategoryType, RotationType
from app.models.user import User, UserRole
from app.models.appointment import Appointment, AppointmentStatus


@pytest.mark.asyncio
async def test_get_slots_by_category(client: AsyncClient, test_db: AsyncSession):
    """GET /appointments/slots con category_name y category_type: 200, entre 1 y 3 slots, días distintos."""
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
    assert 1 <= len(data) <= 3, f"se esperaban 1-3 slots, se devolvieron {len(data)}"
    for slot in data:
        assert slot["slot_datetime"], "slot_datetime no debe estar vacío"
        assert slot["category_name"] == "Cardiologia"
    days = {d["slot_datetime"][:10] for d in data}
    assert len(days) == len(data), "los slots deben caer en días distintos"


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


@pytest.mark.asyncio
async def test_appointments_me_inactive_user_403(client: AsyncClient, test_db: AsyncSession):
    """GET /appointments/me con usuario inactivo: 403 'User account is not active' (AC2)."""
    inactive_user = User(
        dni="INACTIVO001",
        hashed_password="hashed",
        full_name="Inactivo Uno",
        role=UserRole.PATIENT,
        is_active=False,
    )
    test_db.add(inactive_user)
    await test_db.commit()

    token = create_access_token({"sub": "INACTIVO001", "role": "patient"})

    response = await client.get(
        "/appointments/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "User account is not active"


@pytest.mark.asyncio
async def test_appointments_me_active_user_200(client: AsyncClient, test_db: AsyncSession):
    """GET /appointments/me con usuario activo: 200 y sus citas (AC6)."""
    active_user = User(
        dni="ACTIVO001",
        hashed_password="hashed",
        full_name="Activo Uno",
        role=UserRole.PATIENT,
        is_active=True,
    )
    test_db.add(active_user)
    await test_db.flush()

    appointment = Appointment(
        patient_id=active_user.id,
        appointment_date=datetime.now() + timedelta(days=7),
        specialty="Cardiologia",
        status=AppointmentStatus.SCHEDULED,
    )
    test_db.add(appointment)
    await test_db.commit()

    token = create_access_token({"sub": "ACTIVO001", "role": "patient"})

    response = await client.get(
        "/appointments/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert any(app["patient_name"] == "Activo Uno" and app["specialty"] == "Cardiologia" for app in data)


@pytest.mark.asyncio
async def test_appointments_book_inactive_user_403(client: AsyncClient, test_db: AsyncSession):
    """POST /appointments/book con usuario inactivo: 403 y ninguna fila creada (AC3)."""
    inactive_user = User(
        dni="INACTIVO002",
        hashed_password="hashed",
        full_name="Inactivo Dos",
        role=UserRole.PATIENT,
        is_active=False,
    )
    test_db.add(inactive_user)
    await test_db.commit()

    token = create_access_token({"sub": "INACTIVO002", "role": "patient"})
    appointment_date = datetime.now() + timedelta(days=7)

    response = await client.post(
        "/appointments/book",
        json={
            "category_id": 1,
            "appointment_date": appointment_date.isoformat(),
            "category_name": "Cardiologia",
            "notes": "Sin turno",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "User account is not active"

    result = await test_db.execute(
        select(Appointment).where(Appointment.patient_id == inactive_user.id)
    )
    assert result.scalars().all() == []


@pytest.mark.asyncio
async def test_appointments_cancel_inactive_user_403(client: AsyncClient, test_db: AsyncSession):
    """PUT /appointments/{id}/cancel con usuario inactivo: 403 y cita sigue SCHEDULED (AC4)."""
    inactive_user = User(
        dni="INACTIVO003",
        hashed_password="hashed",
        full_name="Inactivo Tres",
        role=UserRole.PATIENT,
        is_active=False,
    )
    test_db.add(inactive_user)
    await test_db.flush()

    appointment = Appointment(
        patient_id=inactive_user.id,
        appointment_date=datetime.now() + timedelta(days=7),
        specialty="Cardiologia",
        status=AppointmentStatus.SCHEDULED,
    )
    test_db.add(appointment)
    await test_db.commit()

    token = create_access_token({"sub": "INACTIVO003", "role": "patient"})

    response = await client.put(
        f"/appointments/{appointment.id}/cancel",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "User account is not active"

    result = await test_db.execute(select(Appointment).where(Appointment.id == appointment.id))
    stored = result.scalar_one()
    assert stored.status == AppointmentStatus.SCHEDULED


@pytest.mark.asyncio
async def test_appointments_all_inactive_user_403(client: AsyncClient, test_db: AsyncSession):
    """GET /appointments/all con staff inactivo: 403 (AC5)."""
    test_db.add(
        User(
            dni="INACTIVO004",
            hashed_password="hashed",
            full_name="Inactivo Cuatro",
            role=UserRole.STAFF,
            is_active=False,
        )
    )
    await test_db.commit()

    token = create_access_token({"sub": "INACTIVO004", "role": "staff"})

    response = await client.get(
        "/appointments/all",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "User account is not active"


@pytest.mark.asyncio
async def test_appointments_export_inactive_user_403(client: AsyncClient, test_db: AsyncSession):
    """GET /appointments/{id}/export con staff inactivo: 403 (AC5)."""
    owner = User(
        dni="PACIENTE002",
        hashed_password="hashed",
        full_name="Paciente Dueño",
        role=UserRole.PATIENT,
        is_active=True,
    )
    test_db.add(owner)
    await test_db.flush()

    appointment = Appointment(
        patient_id=owner.id,
        appointment_date=datetime.now() + timedelta(days=7),
        specialty="Cardiologia",
        status=AppointmentStatus.SCHEDULED,
    )
    test_db.add(appointment)
    await test_db.commit()

    inactive_staff = User(
        dni="INACTIVO005",
        hashed_password="hashed",
        full_name="Inactivo Cinco",
        role=UserRole.STAFF,
        is_active=False,
    )
    test_db.add(inactive_staff)
    await test_db.commit()

    token = create_access_token({"sub": "INACTIVO005", "role": "staff"})

    response = await client.get(
        f"/appointments/{appointment.id}/export",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "User account is not active"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method,path,body",
    [
        ("GET", "/appointments/me", None),
        ("POST", "/appointments/book", {
            "category_id": 1,
            "appointment_date": (datetime.now() + timedelta(days=7)).isoformat(),
            "category_name": "Cardiologia",
        }),
        ("PUT", "/appointments/999/cancel", None),
        ("GET", "/appointments/all", None),
        ("GET", "/appointments/999/export", None),
    ],
)
async def test_appointments_require_auth(client: AsyncClient, method: str, path: str, body: dict):
    """Sin Authorization header, endpoints autenticados devuelven 401 (AC7). get_slots es público y se excluye."""
    kwargs = {}
    if body is not None:
        kwargs["json"] = body

    response = await client.request(method, path, **kwargs)

    assert response.status_code == 401
