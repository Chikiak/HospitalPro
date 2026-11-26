import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import get_password_hash, verify_password
from app.models.system_config import SystemConfig
from app.models.user import User, UserRole
from app.repositories.allowed_person_repository import AllowedPersonRepository


ADMIN_PASSWORD = "AdminPass1234"
STAFF_PASSWORD = "correct-staff-password"
ADMIN_DNI = "11111111111"
PATIENT_DNI = "22222222222"
STAFF_DNI = "33333333333"


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


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient, test_db: AsyncSession):
    """Test successful user registration."""
    allowed_repo = AllowedPersonRepository(test_db)
    await allowed_repo.bulk_create([{"dni": "12345678901"}])

    response = await client.post(
        "/auth/users/register",
        json={
            "dni": "12345678901",
            "password": "testpassword123",
            "full_name": "Test User",
            "role": "patient",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["dni"] == "12345678901"
    assert data["full_name"] == "Test User"
    assert data["role"] == "patient"
    assert data["is_active"] is True
    assert "id" in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_dni(client: AsyncClient, test_db: AsyncSession):
    """Test registration with duplicate DNI returns 409."""
    allowed_repo = AllowedPersonRepository(test_db)
    await allowed_repo.bulk_create([{"dni": "12345678901"}])

    await client.post(
        "/auth/users/register",
        json={
            "dni": "12345678901",
            "password": "testpassword123",
            "full_name": "Test User",
            "role": "patient",
        },
    )

    response = await client.post(
        "/auth/users/register",
        json={
            "dni": "12345678901",
            "password": "anotherpassword",
            "full_name": "Another User",
            "role": "patient",
        },
    )

    assert response.status_code == 409
    detail = response.json()["detail"].lower()
    assert "ya existe" in detail or "existe" in detail


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_db: AsyncSession):
    """Test successful login."""
    allowed_repo = AllowedPersonRepository(test_db)
    await allowed_repo.bulk_create([{"dni": "12345678901"}])

    await client.post(
        "/auth/users/register",
        json={
            "dni": "12345678901",
            "password": "testpassword123",
            "full_name": "Test User",
            "role": "patient",
        },
    )

    response = await client.post(
        "/auth/login/access-token",
        json={"dni": "12345678901", "password": "testpassword123"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert isinstance(data["access_token"], str)
    assert len(data["access_token"]) > 0


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, test_db: AsyncSession):
    """Test login with wrong password returns 401."""
    allowed_repo = AllowedPersonRepository(test_db)
    await allowed_repo.bulk_create([{"dni": "12345678901"}])

    await client.post(
        "/auth/users/register",
        json={
            "dni": "12345678901",
            "password": "testpassword123",
            "full_name": "Test User",
            "role": "patient",
        },
    )

    response = await client.post(
        "/auth/login/access-token",
        json={"dni": "12345678901", "password": "wrongpassword"},
    )

    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    """Test login with non-existent user returns 401."""
    response = await client.post(
        "/auth/login/access-token",
        json={"dni": "99999999999", "password": "somepassword"},
    )

    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_staff_login_success(client: AsyncClient, test_db: AsyncSession):
    """Test successful staff login with hashed password in system_config."""
    test_db.add(SystemConfig(key="staff_password", value=get_password_hash("correct-staff-password")))
    await test_db.commit()

    response = await client.post(
        "/auth/login/staff",
        json={"password": "correct-staff-password"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert isinstance(data["access_token"], str)
    assert len(data["access_token"]) > 0


@pytest.mark.asyncio
async def test_staff_login_wrong_password(client: AsyncClient, test_db: AsyncSession):
    """Test staff login with wrong password returns 401."""
    test_db.add(SystemConfig(key="staff_password", value=get_password_hash("correct-staff-password")))
    await test_db.commit()

    response = await client.post(
        "/auth/login/staff",
        json={"password": "wrong-password"},
    )

    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


@pytest.mark.asyncio
@pytest.mark.parametrize("role", ["admin", "doctor", "staff"])
async def test_register_ignores_client_role(client: AsyncClient, test_db: AsyncSession, role: str):
    """Registration ignores client-supplied role; always creates patient."""
    allowed_repo = AllowedPersonRepository(test_db)
    await allowed_repo.bulk_create([{"dni": "12345678901"}])

    response = await client.post(
        "/auth/users/register",
        json={
            "dni": "12345678901",
            "password": "securepass123",
            "full_name": "Test User",
            "role": role,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["role"] == "patient"

    result = await test_db.get(User, data["id"])
    assert result is not None
    assert result.role == UserRole.PATIENT


@pytest.mark.asyncio
async def test_auth_error_messages_are_uniform(client: AsyncClient, test_db: AsyncSession, admin_headers: dict):
    """Login, staff login and verify-admin all return the same 401 detail."""
    login_resp = await client.post(
        "/auth/login/access-token",
        json={"dni": "99999999999", "password": "wrongpassword"},
    )
    assert login_resp.status_code == 401
    login_detail = login_resp.json()["detail"]

    test_db.add(SystemConfig(key="staff_password", value=get_password_hash("correct-staff-password")))
    test_db.add(SystemConfig(key="admin_password", value=get_password_hash("admin-password-1234")))
    await test_db.commit()

    staff_resp = await client.post(
        "/auth/login/staff",
        json={"password": "wrong-password"},
    )
    assert staff_resp.status_code == 401
    staff_detail = staff_resp.json()["detail"]

    # verify-admin con token admin y contraseña incorrecta
    verify_resp = await client.post(
        "/auth/verify-admin",
        json={"password": "wrongpassword"},
        headers=admin_headers,
    )
    assert verify_resp.status_code == 401
    verify_detail = verify_resp.json()["detail"]

    assert login_detail == "Credenciales incorrectas"
    assert staff_detail == "Credenciales incorrectas"
    assert verify_detail == "Credenciales incorrectas"


@pytest.mark.asyncio
async def test_staff_login_against_hash(client: AsyncClient, test_db: AsyncSession):
    """staff_password hasheado en system_config: login correcto -> 200 con token."""
    test_db.add(SystemConfig(key="staff_password", value=get_password_hash("correct-staff-password")))
    await test_db.commit()

    response = await client.post(
        "/auth/login/staff",
        json={"password": "correct-staff-password"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


@pytest.mark.asyncio
async def test_staff_login_wrong_password_against_hash(client: AsyncClient, test_db: AsyncSession):
    """staff_password hasheado: contraseña incorrecta -> 401 "Credenciales incorrectas"."""
    test_db.add(SystemConfig(key="staff_password", value=get_password_hash("correct-staff-password")))
    await test_db.commit()

    response = await client.post(
        "/auth/login/staff",
        json={"password": "wrong-password"},
    )

    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_staff_login_plaintext_value_returns_503(client: AsyncClient, test_db: AsyncSession):
    """staff_password en texto plano -> 503 que nombra el script de conversión, sin comparar en plano."""
    test_db.add(SystemConfig(key="staff_password", value="valor-en-texto-plano"))
    await test_db.commit()

    response = await client.post(
        "/auth/login/staff",
        json={"password": "valor-en-texto-plano"},
    )

    assert response.status_code == 503
    assert "hash_config_passwords.py" in response.json()["detail"]


# ── AC7: verify-admin requiere JWT de rol admin ─────────────────────────

@pytest.mark.asyncio
async def test_verify_admin_requires_admin_jwt_no_token(client: AsyncClient):
    """Sin Authorization header: verify-admin → 401."""
    response = await client.post("/auth/verify-admin", json={"password": ADMIN_PASSWORD})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_verify_admin_requires_admin_jwt_patient(client: AsyncClient, patient_headers: dict):
    """Con token patient: verify-admin → 403."""
    response = await client.post("/auth/verify-admin", json={"password": ADMIN_PASSWORD}, headers=patient_headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_verify_admin_requires_admin_jwt_staff(client: AsyncClient, staff_headers: dict):
    """Con token staff: verify-admin → 403."""
    response = await client.post("/auth/verify-admin", json={"password": ADMIN_PASSWORD}, headers=staff_headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_verify_admin_with_admin_jwt(client: AsyncClient, admin_headers: dict, test_db: AsyncSession):
    """Con token admin y contraseña correcta: verify-admin → 200."""
    test_db.add(SystemConfig(key="admin_password", value=get_password_hash(ADMIN_PASSWORD)))
    await test_db.commit()

    response = await client.post("/auth/verify-admin", json={"password": ADMIN_PASSWORD}, headers=admin_headers)
    assert response.status_code == 200
    assert response.json() == {"message": "Admin verified"}


# ── AC7: update-staff-password requiere JWT de rol admin ────────────────

@pytest.mark.asyncio
async def test_update_staff_password_requires_admin_jwt_no_token(client: AsyncClient):
    """Sin Authorization header: update-staff-password → 401."""
    response = await client.post("/auth/update-staff-password", json={"new_staff_password": "NewPass1234"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_staff_password_requires_admin_jwt_patient(client: AsyncClient, patient_headers: dict):
    """Con token patient: update-staff-password → 403."""
    response = await client.post(
        "/auth/update-staff-password",
        json={"new_staff_password": "NewPass1234"},
        headers=patient_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_staff_password_requires_admin_jwt_staff(client: AsyncClient, staff_headers: dict):
    """Con token staff: update-staff-password → 403."""
    response = await client.post(
        "/auth/update-staff-password",
        json={"new_staff_password": "NewPass1234"},
        headers=staff_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_staff_password_stores_hash(
    client: AsyncClient, admin_headers: dict, test_db: AsyncSession
):
    """Con token admin: update-staff-password guarda hash bcrypt y devuelve 200."""
    response = await client.post(
        "/auth/update-staff-password",
        json={"new_staff_password": "NewStaffPass1234"},
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Staff password updated successfully"

    result = await test_db.execute(
        select(SystemConfig).where(SystemConfig.key == "staff_password")
    )
    stored = result.scalar_one_or_none()
    assert stored is not None
    assert stored.value.startswith("$2b$"), stored.value
    assert stored.value != "NewStaffPass1234"
    assert verify_password("NewStaffPass1234", stored.value) is True


# ── AC8: rate limiting en verify-admin (4ª → 429) ───────────────────────

@pytest.mark.asyncio
async def test_verify_admin_rate_limit(
    client: AsyncClient, admin_headers: dict, test_db: AsyncSession
):
    """La 4ª petición POST /auth/verify-admin devuelve 429."""
    test_db.add(SystemConfig(key="admin_password", value=get_password_hash(ADMIN_PASSWORD)))
    await test_db.commit()

    for i in range(3):
        response = await client.post("/auth/verify-admin", json={"password": ADMIN_PASSWORD}, headers=admin_headers)
        assert response.status_code == 200, f"Request {i+1} failed: {response.status_code}"

    response = await client.post("/auth/verify-admin", json={"password": ADMIN_PASSWORD}, headers=admin_headers)
    assert response.status_code == 429


# ── verify-admin contra hash con JWT ────────────────────────────────────

@pytest.mark.asyncio
async def test_verify_admin_against_hash(client: AsyncClient, admin_headers: dict, test_db: AsyncSession):
    """verify-admin con JWT admin: correcto 200, incorrecto 401."""
    test_db.add(SystemConfig(key="admin_password", value=get_password_hash(ADMIN_PASSWORD)))
    await test_db.commit()

    ok = await client.post("/auth/verify-admin", json={"password": ADMIN_PASSWORD}, headers=admin_headers)
    assert ok.status_code == 200
    assert ok.json() == {"message": "Admin verified"}

    bad = await client.post("/auth/verify-admin", json={"password": "wrong-password"}, headers=admin_headers)
    assert bad.status_code == 401
    assert "incorrect" in bad.json()["detail"].lower()


# ── auth error messages uniformes con hashes (con JWT admin) ────────────

@pytest.mark.asyncio
async def test_auth_error_messages_are_uniform_with_hashes(
    client: AsyncClient, admin_headers: dict, test_db: AsyncSession
):
    """Login, staff login y verify-admin devuelven el mismo 401 con valores hasheados."""
    staff_pass = "correct-staff-password"
    admin_pass = "AdminPass1234"
    test_db.add(SystemConfig(key="staff_password", value=get_password_hash(staff_pass)))
    test_db.add(SystemConfig(key="admin_password", value=get_password_hash(admin_pass)))
    await test_db.commit()

    login_resp = await client.post(
        "/auth/login/access-token",
        json={"dni": "99999999999", "password": "wrongpassword"},
    )
    assert login_resp.status_code == 401

    staff_resp = await client.post(
        "/auth/login/staff",
        json={"password": "wrong-password"},
    )
    assert staff_resp.status_code == 401

    verify_resp = await client.post(
        "/auth/verify-admin",
        json={"password": "wrongpassword"},
        headers=admin_headers,
    )
    assert verify_resp.status_code == 401

    assert login_resp.json()["detail"] == "Credenciales incorrectas"
    assert staff_resp.json()["detail"] == "Credenciales incorrectas"
    assert verify_resp.json()["detail"] == "Credenciales incorrectas"


@pytest.mark.asyncio
async def test_staff_login_missing_staff_password_returns_503(client: AsyncClient, test_db: AsyncSession):
    """POST /auth/login/staff sin staff_password en system_config -> 503."""
    response = await client.post(
        "/auth/login/staff",
        json={"password": "whatever"},
    )
    assert response.status_code == 503
    assert "Staff authentication is not configured" in response.json()["detail"]


@pytest.mark.asyncio
async def test_verify_admin_missing_admin_password_returns_503(client: AsyncClient, test_db: AsyncSession):
    """POST /auth/verify-admin sin admin_password en system_config -> 503."""
    response = await client.post(
        "/auth/verify-admin",
        json={"password": "whatever"},
    )
    assert response.status_code == 503
    assert "Admin authentication is not configured" in response.json()["detail"]


@pytest.mark.asyncio
async def test_verify_admin_plaintext_admin_password_returns_503(client: AsyncClient, test_db: AsyncSession):
    """POST /auth/verify-admin con admin_password en texto plano -> 503."""
    test_db.add(SystemConfig(key="admin_password", value="valor-en-texto-plano"))
    await test_db.commit()

    response = await client.post(
        "/auth/verify-admin",
        json={"password": "valor-en-texto-plano"},
    )
    assert response.status_code == 503
    assert "hash_config_passwords.py" in response.json()["detail"]
