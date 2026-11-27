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
    """Test successful staff login against a real, active STAFF user.

    Token `sub` must be the real DNI and the role must be STAFF.
    """
    staff = User(
        dni=STAFF_DNI,
        hashed_password=get_password_hash(STAFF_PASSWORD),
        full_name="Staff User",
        role=UserRole.STAFF,
        is_active=True,
    )
    test_db.add(staff)
    await test_db.commit()

    response = await client.post(
        "/auth/login/staff",
        json={"dni": STAFF_DNI, "password": STAFF_PASSWORD},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert isinstance(data["access_token"], str)
    assert len(data["access_token"]) > 0
    assert data["user"]["dni"] == STAFF_DNI
    assert data["user"]["role"] == "staff"


@pytest.mark.asyncio
async def test_staff_login_wrong_password(client: AsyncClient, test_db: AsyncSession):
    """Test staff login with wrong password returns 401, no oracle."""
    staff = User(
        dni=STAFF_DNI,
        hashed_password=get_password_hash(STAFF_PASSWORD),
        full_name="Staff User",
        role=UserRole.STAFF,
        is_active=True,
    )
    test_db.add(staff)
    await test_db.commit()

    response = await client.post(
        "/auth/login/staff",
        json={"dni": STAFF_DNI, "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciales incorrectas"


def _make_staff_user(test_db: AsyncSession, dni: str = STAFF_DNI, active: bool = True) -> User:
    staff = User(
        dni=dni,
        hashed_password=get_password_hash(STAFF_PASSWORD),
        full_name="Staff User",
        role=UserRole.STAFF,
        is_active=active,
    )
    test_db.add(staff)
    return staff


@pytest.mark.asyncio
async def test_staff_login_nonexistent_dni(client: AsyncClient, test_db: AsyncSession):
    """Unknown DNI returns the same generic 401 (no credential oracle)."""
    response = await client.post(
        "/auth/login/staff",
        json={"dni": "99999999999", "password": "whatever"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciales incorrectas"


@pytest.mark.asyncio
async def test_staff_login_inactive_user(client: AsyncClient, test_db: AsyncSession):
    """Inactive STAFF user returns the same generic 401 (no oracle)."""
    _make_staff_user(test_db, STAFF_DNI, active=False)
    await test_db.commit()

    response = await client.post(
        "/auth/login/staff",
        json={"dni": STAFF_DNI, "password": STAFF_PASSWORD},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciales incorrectas"


@pytest.mark.asyncio
async def test_staff_login_wrong_role(client: AsyncClient, test_db: AsyncSession):
    """A non-STAFF user (e.g. patient) cannot log in via /auth/login/staff."""
    patient = User(
        dni=STAFF_DNI,
        hashed_password=get_password_hash(STAFF_PASSWORD),
        full_name="Patient User",
        role=UserRole.PATIENT,
        is_active=True,
    )
    test_db.add(patient)
    await test_db.commit()

    response = await client.post(
        "/auth/login/staff",
        json={"dni": STAFF_DNI, "password": STAFF_PASSWORD},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciales incorrectas"


@pytest.mark.asyncio
async def test_auth_error_messages_are_uniform(client: AsyncClient, test_db: AsyncSession, admin_headers: dict):
    """Login, staff login and verify-admin all return the same 401 detail."""
    login_resp = await client.post(
        "/auth/login/access-token",
        json={"dni": "99999999999", "password": "wrongpassword"},
    )
    assert login_resp.status_code == 401
    login_detail = login_resp.json()["detail"]

    _make_staff_user(test_db, STAFF_DNI)
    test_db.add(SystemConfig(key="admin_password", value=get_password_hash("admin-password-1234")))
    await test_db.commit()

    staff_resp = await client.post(
        "/auth/login/staff",
        json={"dni": STAFF_DNI, "password": "wrong-password"},
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
async def test_bootstrap_staff_can_login(test_db, client: AsyncClient):
    """Staff provisioned out-of-band via create_admin can log in with real DNI."""
    from scripts.create_admin import ensure_staff

    staff = await ensure_staff(test_db, STAFF_DNI, STAFF_PASSWORD, "Staff Bootstrap")
    assert staff.role == UserRole.STAFF
    assert staff.is_active is True

    response = await client.post(
        "/auth/login/staff",
        json={"dni": STAFF_DNI, "password": STAFF_PASSWORD},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["dni"] == STAFF_DNI
    assert data["user"]["role"] == "staff"


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


# ── update-staff-password requiere JWT de rol admin ──────────────────────

@pytest.mark.asyncio
async def test_update_staff_password_requires_admin_jwt_no_token(client: AsyncClient):
    """Sin Authorization header: update-staff-password → 401 (cuerpo válido)."""
    response = await client.post(
        "/auth/update-staff-password",
        json={"dni": STAFF_DNI, "new_password": "aaaaaaaa"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_staff_password_requires_admin_jwt_patient(client: AsyncClient, patient_headers: dict):
    """Con token patient: update-staff-password → 403."""
    response = await client.post(
        "/auth/update-staff-password",
        json={"dni": STAFF_DNI, "new_password": "aaaaaaaa"},
        headers=patient_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_staff_password_requires_admin_jwt_staff(client: AsyncClient, staff_headers: dict):
    """Con token staff: update-staff-password → 403."""
    response = await client.post(
        "/auth/update-staff-password",
        json={"dni": STAFF_DNI, "new_password": "aaaaaaaa"},
        headers=staff_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
@pytest.mark.parametrize("body", [
    {"new_password": "aaaaaaaa"},                      # sin dni
    {"dni": STAFF_DNI},                                   # sin new_password
    {"dni": "12345", "new_password": "aaaaaaaa"},     # dni mal formado
    {"dni": STAFF_DNI, "new_password": "short"},         # contraseña corta
])
async def test_update_staff_password_validation_errors(client: AsyncClient, admin_headers: dict, body: dict):
    """Cuerpo inválido → 422 sin tocar la base de datos."""
    response = await client.post(
        "/auth/update-staff-password",
        json=body,
        headers=admin_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_staff_password_updates_real_staff_user(
    client: AsyncClient, admin_headers: dict, test_db: AsyncSession
):
    """Con token admin: actualiza la contraseña de un User staff real (no system_config)."""
    staff = User(
        dni=STAFF_DNI,
        hashed_password=get_password_hash("bbbbbbbb"),
        full_name="Staff User",
        role=UserRole.STAFF,
        is_active=True,
    )
    test_db.add(staff)
    await test_db.commit()

    response = await client.post(
        "/auth/update-staff-password",
        json={"dni": STAFF_DNI, "new_password": "aaaaaaaa"},
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Contraseña de personal actualizada correctamente"

    result = await test_db.execute(select(User).where(User.dni == STAFF_DNI))
    user = result.scalar_one()
    assert verify_password("aaaaaaaa", user.hashed_password) is True
    assert verify_password("bbbbbbbb", user.hashed_password) is False


@pytest.mark.asyncio
async def test_update_staff_password_unknown_dni_returns_404(
    client: AsyncClient, admin_headers: dict, test_db: AsyncSession
):
    """DNI inexistente → 404 genérico (sin oráculo de existencia)."""
    response = await client.post(
        "/auth/update-staff-password",
        json={"dni": "99999999999", "new_password": "aaaaaaaa"},
        headers=admin_headers,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Usuario staff no encontrado"


@pytest.mark.asyncio
async def test_update_staff_password_wrong_role_returns_404(
    client: AsyncClient, admin_headers: dict, test_db: AsyncSession
):
    """Un DNI con rol distinto a staff → 404 genérico (sin oráculo de rol)."""
    test_db.add(
        User(
            dni=STAFF_DNI,
            hashed_password=get_password_hash("cccccccc"),
            full_name="Patient User",
            role=UserRole.PATIENT,
            is_active=True,
        )
    )
    await test_db.commit()

    response = await client.post(
        "/auth/update-staff-password",
        json={"dni": STAFF_DNI, "new_password": "aaaaaaaa"},
        headers=admin_headers,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Usuario staff no encontrado"


@pytest.mark.asyncio
async def test_update_staff_password_inactive_staff_returns_404(
    client: AsyncClient, admin_headers: dict, test_db: AsyncSession
):
    """Un staff inactivo → 404 genérico."""
    test_db.add(
        User(
            dni=STAFF_DNI,
            hashed_password=get_password_hash("bbbbbbbb"),
            full_name="Staff User",
            role=UserRole.STAFF,
            is_active=False,
        )
    )
    await test_db.commit()

    response = await client.post(
        "/auth/update-staff-password",
        json={"dni": STAFF_DNI, "new_password": "aaaaaaaa"},
        headers=admin_headers,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Usuario staff no encontrado"


# ── authenticate_staff no revela existencia ni rol por tiempo de respuesta ─

@pytest.mark.asyncio
async def test_authenticate_staff_runs_bcrypt_for_unknown_dni(test_db, monkeypatch):
    """verify_password se ejecuta aunque el DNI no exista (sin oráculo de tiempo)."""
    from app.services.auth_service import AuthService

    calls = []
    original = verify_password

    def recording(plain_password, hashed_password):
        calls.append((plain_password, hashed_password))
        return original(plain_password, hashed_password)

    monkeypatch.setattr("app.services.auth_service.verify_password", recording)

    service = AuthService(test_db)
    result = await service.authenticate_staff("99999999999", "whatever")

    assert result is None
    assert len(calls) == 1  # bcrypt se ejecutó a pesar de DNI desconocido


@pytest.mark.asyncio
async def test_authenticate_staff_runs_bcrypt_for_wrong_role(test_db, monkeypatch):
    """verify_password se ejecuta aunque el rol no sea STAFF."""
    from app.services.auth_service import AuthService

    calls = []
    original = verify_password

    def recording(plain_password, hashed_password):
        calls.append((plain_password, hashed_password))
        return original(plain_password, hashed_password)

    monkeypatch.setattr("app.services.auth_service.verify_password", recording)

    test_db.add(
        User(
            dni=STAFF_DNI,
            hashed_password=get_password_hash(STAFF_PASSWORD),
            full_name="Patient User",
            role=UserRole.PATIENT,
            is_active=True,
        )
    )
    await test_db.commit()

    service = AuthService(test_db)
    result = await service.authenticate_staff(STAFF_DNI, STAFF_PASSWORD)

    assert result is None
    assert len(calls) == 1  # bcrypt se ejecutó aunque el rol es incorrecto


@pytest.mark.asyncio
async def test_dummy_bcrypt_hash_generated_once_and_reused(test_db, monkeypatch):
    """_dummy_bcrypt_hash se genera una sola vez y se reutiliza en llamadas
    posteriores (mismo coste que un camino real: exactamente un verify)."""
    from app.services import auth_service as auth_service_module

    calls = []
    original_get_password_hash = get_password_hash

    def recording(password):
        calls.append(password)
        return original_get_password_hash(password)

    monkeypatch.setattr("app.services.auth_service.get_password_hash", recording)

    # Limpiar el cache para este test (puede estar poblado de tests previos)
    auth_service_module._dummy_bcrypt_hash.cache_clear()

    from app.services.auth_service import AuthService

    service = AuthService(test_db)

    # Primera llamada: DNI desconocido -> genera el dummy una vez + verify
    result1 = await service.authenticate_staff("11111111111", "whatever")
    assert result1 is None

    # Segunda llamada: DNI desconocido de nuevo -> reutiliza el dummy cacheado
    result2 = await service.authenticate_staff("22222222222", "whatever")
    assert result2 is None

    # get_password_hash se ejecutó exactamente una vez (cache hit después)
    assert len(calls) == 1, f"Esperaba 1 generación de hash, hubo {len(calls)}: {calls}"
    cache_info = auth_service_module._dummy_bcrypt_hash.cache_info()
    assert cache_info.hits == 1, f"Esperaba 1 cache hit, hubo {cache_info.hits}"
    assert cache_info.misses == 1, f"Esperaba 1 cache miss, hubo {cache_info.misses}"


# ── login/staff nunca crea la cuenta compartida dni='staff' ──────────────

@pytest.mark.asyncio
async def test_staff_login_never_creates_shared_staff_row(client: AsyncClient, test_db: AsyncSession):
    """POST /auth/login/staff nunca crea una fila compartida dni='staff'."""
    real_staff = User(
        dni=STAFF_DNI,
        hashed_password=get_password_hash(STAFF_PASSWORD),
        full_name="Staff User",
        role=UserRole.STAFF,
        is_active=True,
    )
    test_db.add(real_staff)
    await test_db.commit()

    await client.post(
        "/auth/login/staff",
        json={"dni": STAFF_DNI, "password": STAFF_PASSWORD},
    )
    await client.post(
        "/auth/login/staff",
        json={"dni": "99999999999", "password": "whatever"},
    )

    result = await test_db.execute(select(User).where(User.dni == "staff"))
    assert result.scalar_one_or_none() is None


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


@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_verify_admin_missing_admin_password_returns_503(client: AsyncClient, test_db: AsyncSession, admin_headers: dict):
    """POST /auth/verify-admin sin admin_password en system_config -> 503."""
    response = await client.post(
        "/auth/verify-admin",
        json={"password": "whatever"},
        headers=admin_headers,
    )
    assert response.status_code == 503
    assert "Admin authentication is not configured" in response.json()["detail"]


@pytest.mark.asyncio
async def test_verify_admin_plaintext_admin_password_returns_503(client: AsyncClient, test_db: AsyncSession, admin_headers: dict):
    """POST /auth/verify-admin con admin_password en texto plano -> 503."""
    test_db.add(SystemConfig(key="admin_password", value="valor-en-texto-plano"))
    await test_db.commit()

    response = await client.post(
        "/auth/verify-admin",
        json={"password": "valor-en-texto-plano"},
        headers=admin_headers,
    )
    assert response.status_code == 503
    assert "hash_config_passwords.py" in response.json()["detail"]
