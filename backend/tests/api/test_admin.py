import pytest
import pytest_asyncio
from datetime import time
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.core.config import settings
from app.models.category_schedule import CategorySchedule, CategoryType, RotationType
from app.models.system_config import SystemConfig
from app.models.user import User, UserRole


ADMIN_PASSWORD = settings.ADMIN_PASSWORD
ADMIN_DNI = "11111111111"
PATIENT_DNI = "22222222222"
STAFF_DNI = "33333333333"

ADMIN_WRITE_ENDPOINTS = [
    ("POST", "/admin/schedules"),
    ("POST", "/admin/categories"),
    ("DELETE", "/admin/categories/Cardiology"),
    ("POST", "/admin/allowed-persons"),
]


@pytest_asyncio.fixture(autouse=True)
async def seed_admin_password(test_db: AsyncSession):
    """Sembrar admin_password hasheado en system_config (necesario para verify-admin)."""
    test_db.add(SystemConfig(key="admin_password", value=get_password_hash(ADMIN_PASSWORD)))
    await test_db.commit()


@pytest_asyncio.fixture
async def admin_user(test_db: AsyncSession):
    user = User(dni=ADMIN_DNI, hashed_password="hashed", full_name="Admin User", role=UserRole.ADMIN, is_active=True)
    test_db.add(user)
    await test_db.commit()
    return user


@pytest_asyncio.fixture
async def patient_user(test_db: AsyncSession):
    user = User(dni=PATIENT_DNI, hashed_password="hashed", full_name="Patient User", role=UserRole.PATIENT, is_active=True)
    test_db.add(user)
    await test_db.commit()
    return user


@pytest_asyncio.fixture
async def staff_user(test_db: AsyncSession):
    user = User(dni=STAFF_DNI, hashed_password="hashed", full_name="Staff User", role=UserRole.STAFF, is_active=True)
    test_db.add(user)
    await test_db.commit()
    return user


@pytest.fixture
def admin_token(make_token, admin_user):
    return make_token(dni=ADMIN_DNI, role="admin")


@pytest.fixture
def patient_token(make_token, patient_user):
    return make_token(dni=PATIENT_DNI, role="patient")


@pytest.fixture
def staff_token(make_token, staff_user):
    return make_token(dni=STAFF_DNI, role="staff")


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def patient_headers(patient_token):
    return {"Authorization": f"Bearer {patient_token}"}


@pytest.fixture
def staff_headers(staff_token):
    return {"Authorization": f"Bearer {staff_token}"}


SCHEDULE_PAYLOAD = {
    "category_type": "specialty",
    "name": "Cardiology",
    "day_of_week": 0,
    "start_time": "09:00:00",
    "turn_duration": 30,
    "max_turns_per_block": 4,
    "rotation_type": "fixed",
    "rotation_weeks": 1,
}

CATEGORY_PAYLOAD = {
    "category_type": "specialty",
    "name": "Cardiology",
}

ALLOWED_PERSON_PAYLOAD = {
    "dni": "44444444444",
    "full_name": "Allowed Person",
}


# ── AC1: 401 sin token ──────────────────────────────────────────────────

@pytest.mark.asyncio
@pytest.mark.parametrize("method,path", ADMIN_WRITE_ENDPOINTS)
async def test_admin_endpoints_require_auth(
    client: AsyncClient, method: str, path: str
):
    """Los 4 endpoints admin de escritura devuelven 401 sin Authorization."""
    if method == "POST":
        payload = SCHEDULE_PAYLOAD if path == "/admin/schedules" else (
            CATEGORY_PAYLOAD if path == "/admin/categories" else ALLOWED_PERSON_PAYLOAD
        )
        response = await client.post(path, json=payload)
    else:
        response = await client.delete(path)
    assert response.status_code == 401


# ── AC2: 403 con rol no-admin ───────────────────────────────────────────

@pytest.mark.asyncio
@pytest.mark.parametrize("method,path", ADMIN_WRITE_ENDPOINTS)
async def test_admin_endpoints_require_admin_role(
    client: AsyncClient, method: str, path: str, patient_headers: dict, staff_headers: dict
):
    """Con token patient o staff, los 4 endpoints devuelven 403."""
    for headers in [patient_headers, staff_headers]:
        if method == "POST":
            payload = SCHEDULE_PAYLOAD if path == "/admin/schedules" else (
                CATEGORY_PAYLOAD if path == "/admin/categories" else ALLOWED_PERSON_PAYLOAD
            )
            response = await client.post(path, json=payload, headers=headers)
        else:
            response = await client.delete(path, headers=headers)
        assert response.status_code == 403


# ── AC3: POST /admin/schedules con admin JWT → 201, GET lista ──────────

@pytest.mark.asyncio
async def test_admin_schedule_with_jwt(client: AsyncClient, admin_headers: dict):
    """Admin crea horario (sin admin_password) → 201 y GET lo lista."""
    response = await client.post("/admin/schedules", json=SCHEDULE_PAYLOAD, headers=admin_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Cardiology"
    assert data["day_of_week"] == 0

    list_response = await client.get("/admin/schedules")
    assert list_response.status_code == 200
    schedules = list_response.json()
    assert len(schedules) == 1
    assert schedules[0]["name"] == "Cardiology"


# ── AC4: ciclo de categorías con admin JWT ──────────────────────────────

@pytest.mark.asyncio
async def test_admin_category_lifecycle_with_jwt(
    client: AsyncClient, admin_headers: dict, test_db: AsyncSession
):
    """POST categories 201, POST allowed-persons 201, DELETE categories 200, horarios eliminados."""
    # Crear categoría
    cat_response = await client.post("/admin/categories", json=CATEGORY_PAYLOAD, headers=admin_headers)
    assert cat_response.status_code == 201

    # Añadir persona autorizada
    ap_response = await client.post("/admin/allowed-persons", json=ALLOWED_PERSON_PAYLOAD, headers=admin_headers)
    assert ap_response.status_code == 201

    # DELETE categoría (sin admin_password en URL)
    del_response = await client.delete("/admin/categories/Cardiology", headers=admin_headers)
    assert del_response.status_code == 200

    # Verificar que los horarios de esa categoría se eliminaron
    list_response = await client.get("/admin/schedules")
    assert list_response.status_code == 200
    schedules = list_response.json()
    cardiology_schedules = [s for s in schedules if s["name"] == "Cardiology"]
    assert len(cardiology_schedules) == 0


# ── AC5: admin_password en payload se ignora ────────────────────────────

@pytest.mark.asyncio
async def test_admin_payload_with_admin_password_ignored(
    client: AsyncClient, admin_headers: dict
):
    """Payload con admin_password extra se acepta e ignora (Pydantic extra='ignore')."""
    payload_with_password = {**SCHEDULE_PAYLOAD, "admin_password": "cualquier-cosa"}
    response = await client.post("/admin/schedules", json=payload_with_password, headers=admin_headers)
    assert response.status_code == 201


# ── AC6: DELETE sin admin_password en URL → 200 ─────────────────────────

@pytest.mark.asyncio
async def test_admin_delete_no_password_param(client: AsyncClient, admin_headers: dict):
    """DELETE /admin/categories/{name} sin admin_password en query: 200."""
    response = await client.delete("/admin/categories/Cardiology", headers=admin_headers)
    assert response.status_code == 200


# ── AC8: rate limiting en POST /admin/schedules (11ª → 429) ─────────────

@pytest.mark.asyncio
async def test_admin_rate_limit(client: AsyncClient, admin_headers: dict):
    """La 11ª petición POST /admin/schedules devuelve 429."""
    for i in range(10):
        response = await client.post("/admin/schedules", json=SCHEDULE_PAYLOAD, headers=admin_headers)
        assert response.status_code == 201, f"Request {i+1} failed: {response.status_code}"

    response = await client.post("/admin/schedules", json=SCHEDULE_PAYLOAD, headers=admin_headers)
    assert response.status_code == 429


# ── GET /admin/schedules sigue público (sin cambios) ────────────────────

@pytest.mark.asyncio
async def test_list_schedules_empty(client: AsyncClient, test_db: AsyncSession):
    response = await client.get("/admin/schedules")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


@pytest.mark.asyncio
async def test_list_schedules_with_data(client: AsyncClient, admin_headers: dict):
    # Create multiple schedules with different category types and days
    schedules_to_create = [
        {
            "category_type": "specialty",
            "name": "Cardiology",
            "day_of_week": 0,
            "start_time": "09:00:00",
            "turn_duration": 30,
            "max_turns_per_block": 4,
            "rotation_type": "fixed",
            "rotation_weeks": 1,
        },
        {
            "category_type": "specialty",
            "name": "Neurology",
            "day_of_week": 1,
            "start_time": "10:00:00",
            "turn_duration": 45,
            "max_turns_per_block": 3,
            "rotation_type": "fixed",
            "rotation_weeks": 1,
        },
        {
            "category_type": "laboratory",
            "name": "Blood Test",
            "day_of_week": 2,
            "start_time": "08:00:00",
            "turn_duration": 15,
            "max_turns_per_block": 8,
            "rotation_type": "alternated",
            "rotation_weeks": 2,
        },
    ]
    for schedule_data in schedules_to_create:
        create_response = await client.post("/admin/schedules", json=schedule_data, headers=admin_headers)
        assert create_response.status_code == 201

    list_response = await client.get("/admin/schedules")
    assert list_response.status_code == 200
    data = list_response.json()
    assert isinstance(data, list)
    assert len(data) == 3

    # Verify ordering (by category_type, then day_of_week)
    # Laboratory comes before Specialty alphabetically
    assert data[0]["category_type"] == "laboratory"
    assert data[0]["day_of_week"] == 2
    assert data[1]["category_type"] == "specialty"
    assert data[1]["day_of_week"] == 0
    assert data[2]["category_type"] == "specialty"
    assert data[2]["day_of_week"] == 1


# ── Tests funcionales restaurados (sin admin_password, con admin JWT) ─────

@pytest.mark.asyncio
async def test_create_schedule_specialty(client: AsyncClient, test_db: AsyncSession, admin_headers: dict):
    """Test creating a new specialty schedule (admin JWT, no admin_password)."""
    response = await client.post(
        "/admin/schedules",
        json={
            "category_type": "specialty",
            "name": "Cardiology",
            "day_of_week": 0,  # Monday
            "start_time": "09:00:00",
            "turn_duration": 30,
            "max_turns_per_block": 4,
            "rotation_type": "fixed",
            "rotation_weeks": 1,
        },
        headers=admin_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["category_type"] == "specialty"
    assert data["name"] == "Cardiology"
    assert data["day_of_week"] == 0
    assert data["start_time"] == "09:00:00"
    assert data["turn_duration"] == 30
    assert data["max_turns_per_block"] == 4
    assert data["rotation_type"] == "fixed"
    assert data["rotation_weeks"] == 1
    assert "id" in data


@pytest.mark.asyncio
async def test_create_schedule_laboratory(client: AsyncClient, test_db: AsyncSession, admin_headers: dict):
    """Test creating a new laboratory schedule (admin JWT, no admin_password)."""
    response = await client.post(
        "/admin/schedules",
        json={
            "category_type": "laboratory",
            "name": "Blood Test",
            "day_of_week": 2,  # Wednesday
            "start_time": "08:00:00",
            "turn_duration": 15,
            "max_turns_per_block": 8,
            "rotation_type": "alternated",
            "rotation_weeks": 2,
        },
        headers=admin_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["category_type"] == "laboratory"
    # El validador de CategoryScheduleCreate fuerza el nombre de laboratorio
    assert data["name"] == "Laboratorio"
    assert data["day_of_week"] == 2
    assert data["rotation_type"] == "alternated"
    assert data["rotation_weeks"] == 2


@pytest.mark.asyncio
async def test_update_existing_schedule(client: AsyncClient, test_db: AsyncSession, admin_headers: dict):
    """Test updating an existing schedule (same category_type and day_of_week)."""
    # Create initial schedule
    initial_response = await client.post(
        "/admin/schedules",
        json={
            "category_type": "specialty",
            "name": "Neurology",
            "day_of_week": 1,  # Tuesday
            "start_time": "10:00:00",
            "turn_duration": 45,
            "max_turns_per_block": 3,
            "rotation_type": "fixed",
            "rotation_weeks": 1,
        },
        headers=admin_headers,
    )
    assert initial_response.status_code == 201
    initial_data = initial_response.json()
    schedule_id = initial_data["id"]

    # Update with different values but same name and day_of_week
    # (el endpoint solo reutiliza el registro si coinciden name y day_of_week)
    update_response = await client.post(
        "/admin/schedules",
        json={
            "category_type": "specialty",
            "name": "Neurology",  # Same name -> matches existing record
            "day_of_week": 1,  # Same Tuesday
            "start_time": "14:00:00",  # Updated time
            "turn_duration": 60,  # Updated duration
            "max_turns_per_block": 5,  # Updated max turns
            "rotation_type": "alternated",  # Updated rotation
            "rotation_weeks": 2,  # Updated weeks
        },
        headers=admin_headers,
    )

    assert update_response.status_code == 201
    updated_data = update_response.json()

    # Should have the same ID (updated in place, not created new)
    assert updated_data["id"] == schedule_id
    assert updated_data["name"] == "Neurology"
    assert updated_data["start_time"] == "14:00:00"
    assert updated_data["turn_duration"] == 60
    assert updated_data["max_turns_per_block"] == 5
    assert updated_data["rotation_type"] == "alternated"
    assert updated_data["rotation_weeks"] == 2


@pytest.mark.asyncio
async def test_different_category_types_same_day(client: AsyncClient, admin_headers: dict):
    """Test creating schedules for different category types on the same day."""
    # Create specialty schedule for Monday
    specialty_response = await client.post(
        "/admin/schedules",
        json={
            "category_type": "specialty",
            "name": "Dermatology",
            "day_of_week": 0,  # Monday
            "start_time": "09:00:00",
            "turn_duration": 30,
            "max_turns_per_block": 4,
            "rotation_type": "fixed",
            "rotation_weeks": 1,
        },
        headers=admin_headers,
    )
    assert specialty_response.status_code == 201

    # Create laboratory schedule for Monday (different category_type)
    lab_response = await client.post(
        "/admin/schedules",
        json={
            "category_type": "laboratory",
            "name": "X-Ray",
            "day_of_week": 0,  # Monday (same day)
            "start_time": "08:00:00",
            "turn_duration": 20,
            "max_turns_per_block": 6,
            "rotation_type": "fixed",
            "rotation_weeks": 1,
        },
        headers=admin_headers,
    )
    assert lab_response.status_code == 201

    # Both should exist independently
    specialty_data = specialty_response.json()
    lab_data = lab_response.json()
    assert specialty_data["id"] != lab_data["id"]
    assert specialty_data["category_type"] == "specialty"
    assert lab_data["category_type"] == "laboratory"


@pytest.mark.asyncio
async def test_create_schedule_invalid_day_of_week(client: AsyncClient, admin_headers: dict):
    """Test creating schedule with invalid day_of_week: 422 por day_of_week."""
    response = await client.post(
        "/admin/schedules",
        json={
            "category_type": "specialty",
            "name": "Cardiology",
            "day_of_week": 7,  # Invalid (should be 0-6)
            "start_time": "09:00:00",
            "turn_duration": 30,
            "max_turns_per_block": 4,
            "rotation_type": "fixed",
            "rotation_weeks": 1,
        },
        headers=admin_headers,
    )

    assert response.status_code == 422  # Validation error
    detail = str(response.json()["detail"])
    assert "day_of_week" in detail, f"se esperaba error en day_of_week, detalle: {detail}"


@pytest.mark.asyncio
async def test_create_schedule_invalid_turn_duration(client: AsyncClient, admin_headers: dict):
    """Test creating schedule with invalid turn_duration: 422 por turn_duration."""
    response = await client.post(
        "/admin/schedules",
        json={
            "category_type": "specialty",
            "name": "Cardiology",
            "day_of_week": 0,
            "start_time": "09:00:00",
            "turn_duration": 0,  # Invalid (should be > 0)
            "max_turns_per_block": 4,
            "rotation_type": "fixed",
            "rotation_weeks": 1,
        },
        headers=admin_headers,
    )

    assert response.status_code == 422  # Validation error
    detail = str(response.json()["detail"])
    assert "turn_duration" in detail, f"se esperaba error en turn_duration, detalle: {detail}"


@pytest.mark.asyncio
async def test_create_schedule_default_rotation_weeks(client: AsyncClient, test_db: AsyncSession, admin_headers: dict):
    """Test creating schedule with default rotation_weeks."""
    response = await client.post(
        "/admin/schedules",
        json={
            "category_type": "specialty",
            "name": "Orthopedics",
            "day_of_week": 3,
            "start_time": "11:00:00",
            "turn_duration": 40,
            "max_turns_per_block": 5,
            "rotation_type": "fixed",
            # rotation_weeks not specified, should default to 1
        },
        headers=admin_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["rotation_weeks"] == 1  # Default value
