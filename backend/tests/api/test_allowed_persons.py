import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.allowed_person_repository import AllowedPersonRepository


@pytest.mark.asyncio
async def test_register_with_allowed_dni(client: AsyncClient, test_db: AsyncSession):
    """Test that registration succeeds with an allowed DNI."""
    # First, add the DNI to the allowed list
    allowed_repo = AllowedPersonRepository(test_db)
    await allowed_repo.bulk_create([{"dni": "12345678901", "full_name": "Test User"}])
    
    # Now try to register with this DNI
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
    
    # Verify DNI is marked as registered
    allowed_person = await allowed_repo.get_by_dni("12345678901")
    assert allowed_person is not None
    assert allowed_person.is_registered is True


@pytest.mark.asyncio
async def test_register_with_unauthorized_dni(client: AsyncClient, test_db: AsyncSession):
    """Test that registration fails with an unauthorized DNI."""
    response = await client.post(
        "/auth/users/register",
        json={
            "dni": "99999999999",
            "password": "testpassword123",
            "full_name": "Unauthorized User",
            "role": "patient",
        },
    )
    
    assert response.status_code == 403
    data = response.json()
    assert "DNI no autorizado" in data["detail"]


@pytest.mark.asyncio
async def test_register_non_patient_without_whitelist(client: AsyncClient, test_db: AsyncSession):
    """Test that non-patient roles can register without being on whitelist."""
    response = await client.post(
        "/auth/users/register",
        json={
            "dni": "doctordni001",
            "password": "doctorpass123",
            "full_name": "Dr. Juan Perez",
            "role": "doctor",
        },
    )
    
    # Should succeed because whitelist check only applies to patients
    assert response.status_code == 201
    data = response.json()
    assert data["role"] == "doctor"


@pytest.mark.asyncio
async def test_bulk_create_allowed_persons(client: AsyncClient, test_db: AsyncSession):
    """Test bulk creation of allowed persons."""
    response = await client.post(
        "/patients/allowed-persons/bulk",
        json={
            "persons": [
                {"dni": "11111111111", "full_name": "Person One"},
                {"dni": "22222222222", "full_name": "Person Two"},
                {"dni": "33333333333"},
            ]
        },
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["count"] == 3
    
    # Verify they were created
    allowed_repo = AllowedPersonRepository(test_db)
    person1 = await allowed_repo.get_by_dni("11111111111")
    assert person1 is not None
    assert person1.full_name == "Person One"
    assert person1.is_registered is False
    
    person3 = await allowed_repo.get_by_dni("33333333333")
    assert person3 is not None
    assert person3.full_name is None


@pytest.mark.asyncio
async def test_is_dni_allowed(test_db: AsyncSession):
    """Test the is_dni_allowed repository method."""
    allowed_repo = AllowedPersonRepository(test_db)
    
    # Add a DNI
    await allowed_repo.bulk_create([{"dni": "12345678901"}])
    
    # Check it's allowed
    assert await allowed_repo.is_dni_allowed("12345678901") is True
    
    # Check a non-existent DNI
    assert await allowed_repo.is_dni_allowed("99999999999") is False


@pytest.mark.asyncio
async def test_mark_as_registered(test_db: AsyncSession):
    """Test marking a DNI as registered."""
    allowed_repo = AllowedPersonRepository(test_db)
    
    # Add a DNI
    await allowed_repo.bulk_create([{"dni": "12345678901"}])
    
    # Verify it's not registered initially
    person = await allowed_repo.get_by_dni("12345678901")
    assert person.is_registered is False
    
    # Mark as registered
    await allowed_repo.mark_as_registered("12345678901")
    
    # Verify it's now registered
    person = await allowed_repo.get_by_dni("12345678901")
    assert person.is_registered is True
