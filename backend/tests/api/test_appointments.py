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
    """POST /appointments/book con categoría válida, nombre correspondiente, fecha futura y franja exacta: 201."""
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

    target = datetime.now() + timedelta(days=7)
    category = CategorySchedule(
        category_type=CategoryType.SPECIALTY,
        name="Cardiologia",
        day_of_week=target.weekday(),
        start_time=time(9, 0),
        turn_duration=30,
        max_turns_per_block=2,
        rotation_type=RotationType.FIXED,
    )
    test_db.add(category)
    await test_db.commit()
    await test_db.refresh(category)

    token = make_token(dni=dni, role="patient")
    appointment_date = target.replace(hour=9, minute=0, second=0, microsecond=0)

    response = await client.post(
        "/appointments/book",
        json={
            "category_id": category.id,
            "appointment_date": appointment_date.isoformat(),
            "category_name": "Cardiologia",
            "notes": "Primera visita",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["specialty"] == "Cardiologia"
    assert data["status"] == "scheduled"
    assert data["patient_name"] == "Paciente Prueba"
    assert data["notes"] == "Primera visita"
    assert "id" in data


@pytest.mark.asyncio
async def test_book_appointment_category_not_found_404(client: AsyncClient, test_db: AsyncSession, make_token):
    """POST /appointments/book con category_id inexistente: 404."""
    dni = "PACIENTE002"
    test_db.add(
        User(dni=dni, hashed_password="hashed", full_name="Paciente Dos", role=UserRole.PATIENT, is_active=True)
    )
    await test_db.commit()

    token = make_token(dni=dni, role="patient")
    response = await client.post(
        "/appointments/book",
        json={
            "category_id": 99999,
            "appointment_date": (datetime.now() + timedelta(days=7)).isoformat(),
            "category_name": "Cardiologia",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404, response.text


@pytest.mark.asyncio
async def test_book_appointment_category_name_mismatch_422(client: AsyncClient, test_db: AsyncSession, make_token):
    """POST /appointments/book con category_name que no corresponde al category_id: 422."""
    dni = "PACIENTE003"
    test_db.add(
        User(dni=dni, hashed_password="hashed", full_name="Paciente Tres", role=UserRole.PATIENT, is_active=True)
    )
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

    # Obtener el id real de la categoría creada
    from sqlalchemy import select

    result = await test_db.execute(select(CategorySchedule).where(CategorySchedule.name == "Cardiologia"))
    category = result.scalar_one()

    token = make_token(dni=dni, role="patient")
    response = await client.post(
        "/appointments/book",
        json={
            "category_id": category.id,
            "appointment_date": (datetime.now() + timedelta(days=7)).isoformat(),
            "category_name": "Traumatologia",  # no coincide con el category_id
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422, response.text


@pytest.mark.asyncio
async def test_book_appointment_past_date_422(client: AsyncClient, test_db: AsyncSession, make_token):
    """POST /appointments/book con fecha en el pasado: 422."""
    dni = "PACIENTE004"
    test_db.add(
        User(dni=dni, hashed_password="hashed", full_name="Paciente Cuatro", role=UserRole.PATIENT, is_active=True)
    )
    await test_db.commit()

    token = make_token(dni=dni, role="patient")
    target = datetime.now() + timedelta(days=7)
    test_db.add(
        CategorySchedule(
            category_type=CategoryType.SPECIALTY,
            name="Cardiologia",
            day_of_week=target.weekday(),
            start_time=time(9, 0),
            turn_duration=30,
            max_turns_per_block=1,
            rotation_type=RotationType.FIXED,
        )
    )
    await test_db.commit()
    from sqlalchemy import select

    result = await test_db.execute(select(CategorySchedule).where(CategorySchedule.name == "Cardiologia"))
    category = result.scalar_one()

    response = await client.post(
        "/appointments/book",
        json={
            "category_id": category.id,
            "appointment_date": (datetime.now() - timedelta(days=1)).isoformat(),
            "category_name": "Cardiologia",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422, response.text


@pytest.mark.asyncio
async def test_book_appointment_invalid_slot_422(client: AsyncClient, test_db: AsyncSession, make_token):
    """POST /appointments/book con fecha futura que no cae en una franja exacta del CategorySchedule: 422."""
    dni = "PACIENTE005"
    test_db.add(
        User(dni=dni, hashed_password="hashed", full_name="Paciente Cinco", role=UserRole.PATIENT, is_active=True)
    )
    target = datetime.now() + timedelta(days=7)
    test_db.add(
        CategorySchedule(
            category_type=CategoryType.SPECIALTY,
            name="Cardiologia",
            day_of_week=target.weekday(),
            start_time=time(9, 0),
            turn_duration=30,
            max_turns_per_block=2,
            rotation_type=RotationType.FIXED,
        )
    )
    await test_db.commit()

    from sqlalchemy import select

    result = await test_db.execute(select(CategorySchedule).where(CategorySchedule.name == "Cardiologia"))
    category = result.scalar_one()

    # 9:25 no es una franja válida (franjas: 9:00, 9:30)
    token = make_token(dni=dni, role="patient")
    invalid_date = target.replace(hour=9, minute=25, second=0, microsecond=0)
    response = await client.post(
        "/appointments/book",
        json={
            "category_id": category.id,
            "appointment_date": invalid_date.isoformat(),
            "category_name": "Cardiologia",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422, response.text


@pytest.mark.asyncio
async def test_book_appointment_capacity_full_409(client: AsyncClient, test_db: AsyncSession, make_token):
    """POST /appointments/book cuando el cupo del slot está agotado: 409 (no sobreventa)."""
    dni_owner = "PACIENTE006"
    dni_other = "PACIENTE007"
    for dni, name in ((dni_owner, "Dueño"), (dni_other, "Otro")):
        test_db.add(User(dni=dni, hashed_password="hashed", full_name=name, role=UserRole.PATIENT, is_active=True))
    await test_db.commit()

    target = datetime.now() + timedelta(days=7)
    test_db.add(
        CategorySchedule(
            category_type=CategoryType.SPECIALTY,
            name="Cardiologia",
            day_of_week=target.weekday(),
            start_time=time(9, 0),
            turn_duration=30,
            max_turns_per_block=1,  # un solo cupo
            rotation_type=RotationType.FIXED,
        )
    )
    await test_db.commit()

    from sqlalchemy import select

    result = await test_db.execute(select(CategorySchedule).where(CategorySchedule.name == "Cardiologia"))
    category = result.scalar_one()
    result = await test_db.execute(select(User).where(User.dni == dni_owner))
    owner = result.scalar_one()

    slot = target.replace(hour=9, minute=0, second=0, microsecond=0)

    # El dueño ocupa el único cupo (insert directo: estado previo).
    test_db.add(
        Appointment(
            patient_id=owner.id,
            appointment_date=slot,
            specialty="Cardiologia",
            status=AppointmentStatus.SCHEDULED,
        )
    )
    await test_db.commit()

    token = make_token(dni=dni_other, role="patient")
    response = await client.post(
        "/appointments/book",
        json={
            "category_id": category.id,
            "appointment_date": slot.isoformat(),
            "category_name": "Cardiologia",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 409, response.text


@pytest.mark.asyncio
async def test_book_appointment_laboratory_capacity_respected(client: AsyncClient, test_db: AsyncSession, make_token):
    """Laboratorio permite hasta max_turns_per_block citas en la misma franja; la siguiente es 409."""
    dni = "PACIENTE008"
    test_db.add(User(dni=dni, hashed_password="hashed", full_name="Paciente Ocho", role=UserRole.PATIENT, is_active=True))
    await test_db.commit()

    target = datetime.now() + timedelta(days=7)
    test_db.add(
        CategorySchedule(
            category_type=CategoryType.LABORATORY,
            name="Laboratorio",
            day_of_week=target.weekday(),
            start_time=time(8, 0),
            turn_duration=15,
            max_turns_per_block=3,  # tres cupos en la misma franja
            rotation_type=RotationType.FIXED,
        )
    )
    await test_db.commit()

    from sqlalchemy import select

    result = await test_db.execute(select(CategorySchedule).where(CategorySchedule.name == "Laboratorio"))
    category = result.scalar_one()
    result = await test_db.execute(select(User).where(User.dni == dni))
    patient = result.scalar_one()

    slot = target.replace(hour=8, minute=0, second=0, microsecond=0)
    token = make_token(dni=dni, role="patient")

    # Ocupo los 3 cupos (dos por insert directo, una por el endpoint).
    for _ in range(2):
        test_db.add(
            Appointment(
                patient_id=patient.id,
                appointment_date=slot,
                specialty="Laboratorio",
                status=AppointmentStatus.SCHEDULED,
            )
        )
    await test_db.commit()

    # La tercera sí cabe.
    response = await client.post(
        "/appointments/book",
        json={
            "category_id": category.id,
            "appointment_date": slot.isoformat(),
            "category_name": "Laboratorio",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201, response.text

    # La cuarta se excede: 409.
    response = await client.post(
        "/appointments/book",
        json={
            "category_id": category.id,
            "appointment_date": slot.isoformat(),
            "category_name": "Laboratorio",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 409, response.text


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


@pytest.mark.asyncio
async def test_book_appointment_inactive_rotation_week_422(client: AsyncClient, test_db: AsyncSession, make_token):
    """Slot en semana alternada INACTIVA (rotation_weeks=2, semana 1): 422 aunque sea futuro."""
    dni = "PACIENTE_ROT1"
    test_db.add(
        User(dni=dni, hashed_password="hashed", full_name="Paciente Rot", role=UserRole.PATIENT, is_active=True)
    )
    await test_db.commit()

    start_date = datetime.now().date()
    target_weekday = datetime.now().weekday()
    # Misma hora/día de semana, pero la semana siguiente (semana 1 -> inactiva con rotation_weeks=2)
    inactive_date = (datetime.now() + timedelta(days=7)).replace(hour=9, minute=0, second=0, microsecond=0)

    test_db.add(
        CategorySchedule(
            category_type=CategoryType.SPECIALTY,
            name="Rotacion Inactiva",
            day_of_week=target_weekday,
            start_time=time(9, 0),
            turn_duration=30,
            max_turns_per_block=2,
            rotation_type=RotationType.ALTERNATED,
            rotation_weeks=2,
            start_date=start_date,
        )
    )
    await test_db.commit()

    result = await test_db.execute(select(CategorySchedule).where(CategorySchedule.name == "Rotacion Inactiva"))
    category = result.scalar_one()

    token = make_token(dni=dni, role="patient")
    response = await client.post(
        "/appointments/book",
        json={
            "category_id": category.id,
            "appointment_date": inactive_date.isoformat(),
            "category_name": "Rotacion Inactiva",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422, response.text


@pytest.mark.asyncio
async def test_book_appointment_before_start_date_422(client: AsyncClient, test_db: AsyncSession, make_token):
    """Slot futuro pero anterior a start_date del calendario: 422 (calendario aún no activo)."""
    dni = "PACIENTE_ROT2"
    test_db.add(
        User(dni=dni, hashed_password="hashed", full_name="Paciente Rot2", role=UserRole.PATIENT, is_active=True)
    )
    await test_db.commit()

    start_date = (datetime.now() + timedelta(days=30)).date()  # empieza dentro de 30 días
    target_weekday = datetime.now().weekday()
    booking_date = (datetime.now() + timedelta(days=7)).replace(hour=9, minute=0, second=0, microsecond=0)
    # booking_date es futuro, pero anterior a start_date -> calendario inactivo

    test_db.add(
        CategorySchedule(
            category_type=CategoryType.SPECIALTY,
            name="Rotacion Futura",
            day_of_week=target_weekday,
            start_time=time(9, 0),
            turn_duration=30,
            max_turns_per_block=2,
            rotation_type=RotationType.ALTERNATED,
            rotation_weeks=2,
            start_date=start_date,
        )
    )
    await test_db.commit()

    result = await test_db.execute(select(CategorySchedule).where(CategorySchedule.name == "Rotacion Futura"))
    category = result.scalar_one()

    token = make_token(dni=dni, role="patient")
    response = await client.post(
        "/appointments/book",
        json={
            "category_id": category.id,
            "appointment_date": booking_date.isoformat(),
            "category_name": "Rotacion Futura",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422, response.text


@pytest.mark.asyncio
async def test_book_appointment_specialty_same_day_another_hour_409(client: AsyncClient, test_db: AsyncSession, make_token):
    """SPECIALTY: una cita activa por especialidad y día; segunda cita otro horario mismo día -> 409."""
    dni_owner = "PACIENTE_SD1"
    dni_other = "PACIENTE_SD2"
    for dni, name in ((dni_owner, "Dueño"), (dni_other, "Otro")):
        test_db.add(User(dni=dni, hashed_password="hashed", full_name=name, role=UserRole.PATIENT, is_active=True))
    await test_db.commit()

    target = datetime.now() + timedelta(days=7)
    test_db.add(
        CategorySchedule(
            category_type=CategoryType.SPECIALTY,
            name="Especialidad Unica",
            day_of_week=target.weekday(),
            start_time=time(9, 0),
            turn_duration=30,
            max_turns_per_block=4,
            rotation_type=RotationType.FIXED,
        )
    )
    await test_db.commit()

    result = await test_db.execute(select(CategorySchedule).where(CategorySchedule.name == "Especialidad Unica"))
    category = result.scalar_one()
    result = await test_db.execute(select(User).where(User.dni == dni_owner))
    owner = result.scalar_one()

    slot1 = target.replace(hour=9, minute=0, second=0, microsecond=0)
    slot2 = target.replace(hour=10, minute=0, second=0, microsecond=0)  # mismo día, otra hora

    # El dueño ocupa el día (una cita por especialidad/día)
    test_db.add(
        Appointment(
            patient_id=owner.id,
            appointment_date=slot1,
            specialty="Especialidad Unica",
            status=AppointmentStatus.SCHEDULED,
        )
    )
    await test_db.commit()

    token = make_token(dni=dni_other, role="patient")
    response = await client.post(
        "/appointments/book",
        json={
            "category_id": category.id,
            "appointment_date": slot2.isoformat(),
            "category_name": "Especialidad Unica",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 409, response.text
