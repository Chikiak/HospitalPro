import pytest
from httpx import AsyncClient
from unittest.mock import patch

from app.models.user import UserRole


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    """Test successful user registration."""
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
async def test_register_duplicate_dni(client: AsyncClient):
    """Test registration with duplicate DNI returns 409."""
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
    assert "already exists" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Test successful login."""
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
async def test_login_wrong_password(client: AsyncClient):
    """Test login with wrong password returns 401."""
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
async def test_staff_login_success(client: AsyncClient):
    """Test successful staff login."""
    with patch("app.api.endpoints.auth.settings.STAFF_PASSWORD", "correct-staff-password"):
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
async def test_staff_login_wrong_password(client: AsyncClient):
    """Test staff login with wrong password returns 401."""
    with patch("app.api.endpoints.auth.settings.STAFF_PASSWORD", "correct-staff-password"):
        response = await client.post(
            "/auth/login/staff",
            json={
                "password": "wrong-password",
            },
        )
        
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()
