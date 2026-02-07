"""Tests for authentication and authorization middleware."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.user import UserRole
from app.repositories.allowed_person_repository import AllowedPersonRepository


@pytest.mark.asyncio
async def test_unauthenticated_access_returns_401(client: AsyncClient):
    """Test that accessing protected endpoints without token returns 401."""
    # Try to access patient list without authentication
    response = await client.get("/patients/")
    assert response.status_code == 401
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_invalid_token_returns_401(client: AsyncClient):
    """Test that invalid token returns 401."""
    headers = {"Authorization": "Bearer invalid_token_here"}
    response = await client.get("/patients/", headers=headers)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_patient_cannot_access_admin_endpoints(client: AsyncClient, test_db: AsyncSession):
    """Test that patients cannot access admin-only endpoints."""
    # Create a patient user
    allowed_repo = AllowedPersonRepository(test_db)
    await allowed_repo.bulk_create([{"dni": "11111111111"}])
    
    patient_response = await client.post(
        "/auth/users/register",
        json={
            "dni": "11111111111",
            "password": "testpass123",
            "full_name": "Patient User",
            "role": "patient",
        },
    )
    assert patient_response.status_code == 201
    
    # Create token for patient
    token = create_access_token({"sub": "11111111111", "role": "patient"})
    headers = {"Authorization": f"Bearer {token}"}
    
    # Try to access patient list (admin/staff/doctor only)
    response = await client.get("/patients/", headers=headers)
    assert response.status_code == 403
    assert "Insufficient permissions" in response.json()["detail"]


@pytest.mark.asyncio
async def test_patient_cannot_access_other_patient_data(client: AsyncClient, test_db: AsyncSession):
    """Test that patients cannot access other patients' medical records."""
    # Create two patients
    allowed_repo = AllowedPersonRepository(test_db)
    await allowed_repo.bulk_create([
        {"dni": "11111111111"},
        {"dni": "22222222222"},
    ])
    
    patient1_response = await client.post(
        "/auth/users/register",
        json={
            "dni": "11111111111",
            "password": "testpass123",
            "full_name": "Patient 1",
            "role": "patient",
        },
    )
    patient1_id = patient1_response.json()["id"]
    
    patient2_response = await client.post(
        "/auth/users/register",
        json={
            "dni": "22222222222",
            "password": "testpass123",
            "full_name": "Patient 2",
            "role": "patient",
        },
    )
    patient2_id = patient2_response.json()["id"]
    
    # Create token for patient 1
    token = create_access_token({"sub": "11111111111", "role": "patient"})
    headers = {"Authorization": f"Bearer {token}"}
    
    # Patient 1 tries to access Patient 2's medical history
    response = await client.get(f"/patients/{patient2_id}/medical-history", headers=headers)
    assert response.status_code == 403
    assert "No tiene permisos" in response.json()["detail"]


@pytest.mark.asyncio
async def test_patient_can_access_own_medical_record(client: AsyncClient, test_db: AsyncSession):
    """Test that patients can access their own medical record."""
    # Create a patient
    allowed_repo = AllowedPersonRepository(test_db)
    await allowed_repo.bulk_create([{"dni": "11111111111"}])
    
    patient_response = await client.post(
        "/auth/users/register",
        json={
            "dni": "11111111111",
            "password": "testpass123",
            "full_name": "Patient User",
            "role": "patient",
        },
    )
    patient_id = patient_response.json()["id"]
    
    # Create token for patient
    token = create_access_token({"sub": "11111111111", "role": "patient"})
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create medical history for the patient
    await client.patch(
        f"/patients/{patient_id}/medical-history",
        json={
            "medical_history": {"condition": "healthy"},
            "allergies": "None",
        },
        headers=headers,
    )
    
    # Patient accesses their own medical history
    response = await client.get(f"/patients/{patient_id}/medical-history", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["patient_id"] == patient_id


@pytest.mark.asyncio
async def test_staff_can_access_all_patients(client: AsyncClient, test_db: AsyncSession):
    """Test that staff can access all patient records."""
    # Create a patient
    allowed_repo = AllowedPersonRepository(test_db)
    await allowed_repo.bulk_create([{"dni": "11111111111", "full_name": "Patient User"}])
    
    patient_response = await client.post(
        "/auth/users/register",
        json={
            "dni": "11111111111",
            "password": "testpass123",
            "full_name": "Patient User",
            "role": "patient",
        },
    )
    patient_id = patient_response.json()["id"]
    
    # Create a staff user
    staff_response = await client.post(
        "/auth/users/register",
        json={
            "dni": "99999999999",
            "password": "staffpass123",
            "full_name": "Staff User",
            "role": "staff",
        },
    )
    
    # Create token for staff
    token = create_access_token({"sub": "99999999999", "role": "staff"})
    headers = {"Authorization": f"Bearer {token}"}
    
    # Staff can access patient list
    response = await client.get("/patients/", headers=headers)
    assert response.status_code == 200
    
    # Create medical history for the patient (using staff token)
    await client.patch(
        f"/patients/{patient_id}/medical-history",
        json={
            "medical_history": {"condition": "test"},
            "allergies": "None",
        },
        headers=headers,
    )
    
    # Staff can access any patient's medical history
    response = await client.get(f"/patients/{patient_id}/medical-history", headers=headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_doctor_can_access_all_patients(client: AsyncClient, test_db: AsyncSession):
    """Test that doctors can access all patient records."""
    # Create a patient
    allowed_repo = AllowedPersonRepository(test_db)
    await allowed_repo.bulk_create([{"dni": "11111111111"}])
    
    patient_response = await client.post(
        "/auth/users/register",
        json={
            "dni": "11111111111",
            "password": "testpass123",
            "full_name": "Patient User",
            "role": "patient",
        },
    )
    patient_id = patient_response.json()["id"]
    
    # Create a doctor user
    await client.post(
        "/auth/users/register",
        json={
            "dni": "88888888888",
            "password": "doctorpass123",
            "full_name": "Doctor User",
            "role": "doctor",
        },
    )
    
    # Create token for doctor
    token = create_access_token({"sub": "88888888888", "role": "doctor"})
    headers = {"Authorization": f"Bearer {token}"}
    
    # Doctor can access patient list
    response = await client.get("/patients/", headers=headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_patient_cannot_add_medical_record_entries(client: AsyncClient, test_db: AsyncSession):
    """Test that patients cannot add medical record entries."""
    # Create a patient
    allowed_repo = AllowedPersonRepository(test_db)
    await allowed_repo.bulk_create([{"dni": "11111111111"}])
    
    patient_response = await client.post(
        "/auth/users/register",
        json={
            "dni": "11111111111",
            "password": "testpass123",
            "full_name": "Patient User",
            "role": "patient",
        },
    )
    patient_id = patient_response.json()["id"]
    
    # Create token for patient
    token = create_access_token({"sub": "11111111111", "role": "patient"})
    headers = {"Authorization": f"Bearer {token}"}
    
    # Patient tries to add medical record entry
    response = await client.post(
        f"/patients/{patient_id}/medical-record/entries",
        json={
            "entry_type": "consultation",
            "specialty": "General",
            "doctor_name": "Dr. Test",
            "diagnosis": "Healthy",
        },
        headers=headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_patient_can_download_own_pdf(client: AsyncClient, test_db: AsyncSession):
    """Test that patients can download their own medical record PDF."""
    # Create a patient and medical record
    allowed_repo = AllowedPersonRepository(test_db)
    await allowed_repo.bulk_create([{"dni": "11111111111"}])
    
    patient_response = await client.post(
        "/auth/users/register",
        json={
            "dni": "11111111111",
            "password": "testpass123",
            "full_name": "Patient User",
            "role": "patient",
        },
    )
    patient_id = patient_response.json()["id"]
    
    # Create token for patient
    token = create_access_token({"sub": "11111111111", "role": "patient"})
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create medical history first
    await client.patch(
        f"/patients/{patient_id}/medical-history",
        json={
            "medical_history": {"condition": "test"},
            "allergies": "None",
        },
        headers=headers,
    )
    
    # Patient can download their own PDF
    response = await client.get(f"/patients/{patient_id}/medical-record/pdf", headers=headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"


@pytest.mark.asyncio
async def test_admin_can_access_allowed_persons_bulk(client: AsyncClient, test_db: AsyncSession):
    """Test that admins can access the allowed persons bulk endpoint."""
    # Create an admin user
    await client.post(
        "/auth/users/register",
        json={
            "dni": "77777777777",
            "password": "adminpass123",
            "full_name": "Admin User",
            "role": "admin",
        },
    )
    
    # Create token for admin
    token = create_access_token({"sub": "77777777777", "role": "admin"})
    headers = {"Authorization": f"Bearer {token}"}
    
    # Admin can access bulk create endpoint
    response = await client.post(
        "/patients/allowed-persons/bulk",
        json={
            "persons": [
                {"dni": "11111111111", "full_name": "Person 1"},
                {"dni": "22222222222", "full_name": "Person 2"},
            ]
        },
        headers=headers,
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_patient_cannot_access_allowed_persons_bulk(client: AsyncClient, test_db: AsyncSession):
    """Test that patients cannot access the allowed persons bulk endpoint."""
    # Create a patient
    allowed_repo = AllowedPersonRepository(test_db)
    await allowed_repo.bulk_create([{"dni": "11111111111"}])
    
    await client.post(
        "/auth/users/register",
        json={
            "dni": "11111111111",
            "password": "testpass123",
            "full_name": "Patient User",
            "role": "patient",
        },
    )
    
    # Create token for patient
    token = create_access_token({"sub": "11111111111", "role": "patient"})
    headers = {"Authorization": f"Bearer {token}"}
    
    # Patient tries to access bulk create endpoint
    response = await client.post(
        "/patients/allowed-persons/bulk",
        json={
            "persons": [
                {"dni": "33333333333", "full_name": "Person 3"},
            ]
        },
        headers=headers,
    )
    assert response.status_code == 403
