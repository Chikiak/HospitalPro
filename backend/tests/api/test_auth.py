import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import get_password_hash, verify_password
from app.models.system_config import SystemConfig
from app.models.user import User, UserRole
from app.repositories.allowed_person_repository import AllowedPersonRepository


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient, test_db: AsyncSession):
    """Test successful user registration."""
    # Add DNI to whitelist
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
    assert "hashed_password" not in data  # Should not expose password


@pytest.mark.asyncio
async def test_register_duplicate_dni(client: AsyncClient, test_db: AsyncSession):
    """Test registration with duplicate DNI returns 409."""
    # Add DNI to whitelist
    allowed_repo = AllowedPersonRepository(test_db)
    await allowed_repo.bulk_create([{"dni": "12345678901"}])
    
    # Register first user
    await client.post(
        "/auth/users/register",
        json={
            "dni": "12345678901",
            "password": "testpassword123",
            "full_name": "Test User",
            "role": "patient",
        },
    )
    
    # Try to register same DNI again
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
    # Check for duplicate user error message
    detail = response.json()["detail"].lower()
    assert "ya existe" in detail or "existe" in detail


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_db: AsyncSession):
    """Test successful login."""
    # Add DNI to whitelist
    allowed_repo = AllowedPersonRepository(test_db)
    await allowed_repo.bulk_create([{"dni": "12345678901"}])
    
    # Register a user first
    await client.post(
        "/auth/users/register",
        json={
            "dni": "12345678901",
            "password": "testpassword123",
            "full_name": "Test User",
            "role": "patient",
        },
    )
    
    # Login with correct credentials
    response = await client.post(
        "/auth/login/access-token",
        json={
            "dni": "12345678901",
            "password": "testpassword123",
        },
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
    # Add DNI to whitelist
    allowed_repo = AllowedPersonRepository(test_db)
    await allowed_repo.bulk_create([{"dni": "12345678901"}])
    
    # Register a user first
    await client.post(
        "/auth/users/register",
        json={
            "dni": "12345678901",
            "password": "testpassword123",
            "full_name": "Test User",
            "role": "patient",
        },
    )
    
    # Try to login with wrong password
    response = await client.post(
        "/auth/login/access-token",
        json={
            "dni": "12345678901",
            "password": "wrongpassword",
        },
    )
    
    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    """Test login with non-existent user returns 401."""
    response = await client.post(
        "/auth/login/access-token",
        json={
            "dni": "99999999999",
            "password": "somepassword",
        },
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
        json={
            "password": "correct-staff-password",
        },
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
        json={
            "password": "wrong-password",
        },
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

    # Verify persisted role is patient
    result = await test_db.get(User, data["id"])
    assert result is not None
    assert result.role == UserRole.PATIENT


@pytest.mark.asyncio
async def test_auth_error_messages_are_uniform(client: AsyncClient, test_db: AsyncSession):
    """Login, staff login and verify-admin all return the same 401 detail."""
    # Login with wrong credentials
    login_resp = await client.post(
        "/auth/login/access-token",
        json={"dni": "99999999999", "password": "wrongpassword"},
    )
    assert login_resp.status_code == 401
    login_detail = login_resp.json()["detail"]

    # Staff login with wrong password (hashed in system_config)
    test_db.add(SystemConfig(key="staff_password", value=get_password_hash("correct-staff-password")))
    test_db.add(SystemConfig(key="admin_password", value=get_password_hash("admin-password-1234")))
    await test_db.commit()

    staff_resp = await client.post(
        "/auth/login/staff",
        json={"password": "wrong-password"},
    )
    assert staff_resp.status_code == 401
    staff_detail = staff_resp.json()["detail"]

    # Verify-admin with wrong password
    verify_resp = await client.post(
        "/auth/verify-admin",
        json={"password": "wrongpassword"},
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


@pytest.mark.asyncio
async def test_update_staff_password_stores_hash(client: AsyncClient, test_db: AsyncSession):
    """AC1: update_staff_password guarda hash bcrypt de la nueva contraseña."""
    admin_pass = "AdminPass1234"
    test_db.add(SystemConfig(key="admin_password", value=get_password_hash(admin_pass)))
    await test_db.commit()

    response = await client.post(
        "/auth/update-staff-password",
        json={
            "admin_password": admin_pass,
            "new_staff_password": "NewPass1234",
        },
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Staff password updated successfully"

    result = await test_db.execute(
        __import__("sqlalchemy").select(SystemConfig).where(SystemConfig.key == "staff_password")
    )
    stored = result.scalar_one_or_none()
    assert stored is not None
    assert stored.value.startswith("$2b$"), stored.value
    assert stored.value != "NewPass1234"
    assert verify_password("NewPass1234", stored.value) is True


@pytest.mark.asyncio
async def test_verify_admin_against_hash(client: AsyncClient, test_db: AsyncSession):
    """AC7: verify_admin contra valor hasheado: correcto 200, incorrecto 401."""
    admin_pass = "AdminPass1234"
    test_db.add(SystemConfig(key="admin_password", value=get_password_hash(admin_pass)))
    await test_db.commit()

    ok = await client.post("/auth/verify-admin", json={"password": admin_pass})
    assert ok.status_code == 200
    assert ok.json() == {"message": "Admin verified"}

    bad = await client.post("/auth/verify-admin", json={"password": "wrong-password"})
    assert bad.status_code == 401
    assert "incorrect" in bad.json()["detail"].lower()


@pytest.mark.asyncio
async def test_auth_error_messages_are_uniform_with_hashes(client: AsyncClient, test_db: AsyncSession):
    """Login, staff login y verify-admin devuelven el mismo 401 con valores hasheados en system_config."""
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
    )
    assert verify_resp.status_code == 401

    assert login_resp.json()["detail"] == "Credenciales incorrectas"
    assert staff_resp.json()["detail"] == "Credenciales incorrectas"
    assert verify_resp.json()["detail"] == "Credenciales incorrectas"
