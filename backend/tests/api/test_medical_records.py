import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.repositories.allowed_person_repository import AllowedPersonRepository
from app.repositories.medical_record_repository import MedicalRecordRepository
from app.repositories.user_repository import UserRepository


@pytest.mark.asyncio
async def test_auto_create_medical_record_on_update_medical_history(
    client: AsyncClient, test_db: AsyncSession
):
    """Test that medical record is auto-created when updating medical history."""
    # First, create an allowed person and register a patient
    allowed_repo = AllowedPersonRepository(test_db)
    await allowed_repo.bulk_create([{"dni": "12345678901", "full_name": "Test Patient"}])
    
    # Register the patient
    register_response = await client.post(
        "/auth/users/register",
        json={
            "dni": "12345678901",
            "password": "testpassword123",
            "full_name": "Test Patient",
            "role": "patient",
        },
    )
    assert register_response.status_code == 201
    patient_id = register_response.json()["id"]
    
    # Create auth token for patient
    token = create_access_token({"sub": "12345678901", "role": "patient"})
    headers = {"Authorization": f"Bearer {token}"}
    
    # Update medical history (this should auto-create the medical record)
    response = await client.patch(
        f"/patients/{patient_id}/medical-history",
        json={
            "medical_history": {
                "chronic_diseases": ["Diabetes", "Hypertension"],
                "allergies": "Penicillin"
            }
        },
        headers=headers,
    )
    assert response.status_code == 200
    
    # Verify medical record was created
    medical_record_repo = MedicalRecordRepository(test_db)
    medical_record = await medical_record_repo.get_by_patient_id(patient_id)
    assert medical_record is not None
    assert medical_record.registration_survey is not None
    assert "chronic_diseases" in medical_record.registration_survey


@pytest.mark.asyncio
async def test_get_medical_record(client: AsyncClient, test_db: AsyncSession):
    """Test getting a patient's medical record."""
    # Setup: Create patient with medical record
    allowed_repo = AllowedPersonRepository(test_db)
    await allowed_repo.bulk_create([{"dni": "12345678901"}])
    
    register_response = await client.post(
        "/auth/users/register",
        json={
            "dni": "12345678901",
            "password": "testpassword123",
            "full_name": "Test Patient",
            "role": "patient",
        },
    )
    patient_id = register_response.json()["id"]
    
    # Create medical record
    medical_record_repo = MedicalRecordRepository(test_db)
    await medical_record_repo.create(
        patient_id=patient_id,
        registration_survey={"allergies": "None", "chronic_diseases": []}
    )
    
    # Create auth token for patient
    token = create_access_token({"sub": "12345678901", "role": "patient"})
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get medical record
    response = await client.get(f"/patients/{patient_id}/medical-record", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["patient_id"] == patient_id
    assert "registration_survey" in data
    assert "entries" in data


@pytest.mark.asyncio
async def test_get_medical_record_not_found(client: AsyncClient, test_db: AsyncSession):
    """Test getting medical record for patient without one."""
    # Create patient without medical record
    allowed_repo = AllowedPersonRepository(test_db)
    await allowed_repo.bulk_create([{"dni": "12345678901"}])
    
    register_response = await client.post(
        "/auth/users/register",
        json={
            "dni": "12345678901",
            "password": "testpassword123",
            "full_name": "Test Patient",
            "role": "patient",
        },
    )
    patient_id = register_response.json()["id"]
    
    # Create auth token for patient
    token = create_access_token({"sub": "12345678901", "role": "patient"})
    headers = {"Authorization": f"Bearer {token}"}
    
    # Try to get medical record
    response = await client.get(f"/patients/{patient_id}/medical-record", headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_add_medical_record_entry_consultation(client: AsyncClient, test_db: AsyncSession):
    """Test adding a consultation entry to medical record."""
    # Setup: Create patient with medical record
    allowed_repo = AllowedPersonRepository(test_db)
    await allowed_repo.bulk_create([{"dni": "12345678901"}])
    
    register_response = await client.post(
        "/auth/users/register",
        json={
            "dni": "12345678901",
            "password": "testpassword123",
            "full_name": "Test Patient",
            "role": "patient",
        },
    )
    patient_id = register_response.json()["id"]
    
    # Create medical record
    medical_record_repo = MedicalRecordRepository(test_db)
    await medical_record_repo.create(patient_id=patient_id)
    
    # Create auth token for staff to add entry
    staff_allowed_repo = AllowedPersonRepository(test_db)
    await staff_allowed_repo.bulk_create([{"dni": "98765432100", "full_name": "Staff User"}])
    staff_register_response = await client.post(
        "/auth/users/register",
        json={
            "dni": "98765432100",
            "password": "staffpassword123",
            "full_name": "Staff User",
            "role": "staff",
        },
    )
    staff_token = create_access_token({"sub": "98765432100", "role": "staff"})
    staff_headers = {"Authorization": f"Bearer {staff_token}"}
    
    # Add consultation entry
    response = await client.post(
        f"/patients/{patient_id}/medical-record/entries",
        json={
            "entry_type": "consultation",
            "specialty": "Cardiology",
            "doctor_name": "Dr. Juan Perez",
            "diagnosis": "Hypertension",
            "notes": "Patient advised to reduce salt intake"
        },
        headers=staff_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["entries"]) == 1
    assert data["entries"][0]["entry_type"] == "consultation"
    assert data["entries"][0]["specialty"] == "Cardiology"
    assert "timestamp" in data["entries"][0]


@pytest.mark.asyncio
async def test_add_medical_record_entry_lab_result(client: AsyncClient, test_db: AsyncSession):
    """Test adding a lab result entry to medical record."""
    # Setup: Create patient with medical record
    allowed_repo = AllowedPersonRepository(test_db)
    await allowed_repo.bulk_create([{"dni": "12345678901"}])
    
    register_response = await client.post(
        "/auth/users/register",
        json={
            "dni": "12345678901",
            "password": "testpassword123",
            "full_name": "Test Patient",
            "role": "patient",
        },
    )
    patient_id = register_response.json()["id"]
    
    # Create medical record
    medical_record_repo = MedicalRecordRepository(test_db)
    await medical_record_repo.create(patient_id=patient_id)
    
    # Create auth token for staff to add entry
    staff_allowed_repo = AllowedPersonRepository(test_db)
    await staff_allowed_repo.bulk_create([{"dni": "98765432100", "full_name": "Staff User"}])
    staff_register_response = await client.post(
        "/auth/users/register",
        json={
            "dni": "98765432100",
            "password": "staffpassword123",
            "full_name": "Staff User",
            "role": "staff",
        },
    )
    staff_token = create_access_token({"sub": "98765432100", "role": "staff"})
    staff_headers = {"Authorization": f"Bearer {staff_token}"}
    
    # Add lab result entry
    response = await client.post(
        f"/patients/{patient_id}/medical-record/entries",
        json={
            "entry_type": "lab_result",
            "specialty": "Laboratory",
            "results": {
                "glucose": "110 mg/dL",
                "cholesterol": "200 mg/dL"
            },
            "notes": "Results within normal range"
        },
        headers=staff_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["entries"]) == 1
    assert data["entries"][0]["entry_type"] == "lab_result"
    assert "results" in data["entries"][0]


@pytest.mark.asyncio
async def test_add_multiple_entries(client: AsyncClient, test_db: AsyncSession):
    """Test adding multiple entries to medical record."""
    # Setup: Create patient with medical record
    allowed_repo = AllowedPersonRepository(test_db)
    await allowed_repo.bulk_create([{"dni": "12345678901"}])
    
    register_response = await client.post(
        "/auth/users/register",
        json={
            "dni": "12345678901",
            "password": "testpassword123",
            "full_name": "Test Patient",
            "role": "patient",
        },
    )
    patient_id = register_response.json()["id"]
    
    # Create medical record
    medical_record_repo = MedicalRecordRepository(test_db)
    await medical_record_repo.create(patient_id=patient_id)
    
    # Create auth token for staff to add entries
    staff_allowed_repo = AllowedPersonRepository(test_db)
    await staff_allowed_repo.bulk_create([{"dni": "98765432100", "full_name": "Staff User"}])
    staff_register_response = await client.post(
        "/auth/users/register",
        json={
            "dni": "98765432100",
            "password": "staffpassword123",
            "full_name": "Staff User",
            "role": "staff",
        },
    )
    staff_token = create_access_token({"sub": "98765432100", "role": "staff"})
    staff_headers = {"Authorization": f"Bearer {staff_token}"}
    
    # Add first entry
    await client.post(
        f"/patients/{patient_id}/medical-record/entries",
        json={
            "entry_type": "consultation",
            "specialty": "General Medicine",
            "diagnosis": "Common cold"
        },
        headers=staff_headers,
    )
    
    # Add second entry
    await client.post(
        f"/patients/{patient_id}/medical-record/entries",
        json={
            "entry_type": "lab_result",
            "results": {"test": "negative"}
        },
        headers=staff_headers,
    )
    
    # Create auth token for patient to get their record
    patient_token = create_access_token({"sub": "12345678901", "role": "patient"})
    patient_headers = {"Authorization": f"Bearer {patient_token}"}
    
    # Get medical record and verify both entries
    response = await client.get(f"/patients/{patient_id}/medical-record", headers=patient_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["entries"]) == 2


@pytest.mark.asyncio
async def test_add_entry_to_nonexistent_medical_record(client: AsyncClient, test_db: AsyncSession):
    """Test that adding entry to non-existent medical record fails."""
    # Create patient without medical record
    allowed_repo = AllowedPersonRepository(test_db)
    await allowed_repo.bulk_create([{"dni": "12345678901"}])
    
    register_response = await client.post(
        "/auth/users/register",
        json={
            "dni": "12345678901",
            "password": "testpassword123",
            "full_name": "Test Patient",
            "role": "patient",
        },
    )
    patient_id = register_response.json()["id"]
    
    # Create auth token for staff
    staff_allowed_repo = AllowedPersonRepository(test_db)
    await staff_allowed_repo.bulk_create([{"dni": "98765432100", "full_name": "Staff User"}])
    staff_register_response = await client.post(
        "/auth/users/register",
        json={
            "dni": "98765432100",
            "password": "staffpassword123",
            "full_name": "Staff User",
            "role": "staff",
        },
    )
    staff_token = create_access_token({"sub": "98765432100", "role": "staff"})
    staff_headers = {"Authorization": f"Bearer {staff_token}"}
    
    # Try to add entry without creating medical record first
    response = await client.post(
        f"/patients/{patient_id}/medical-record/entries",
        json={
            "entry_type": "consultation",
            "diagnosis": "Test"
        },
        headers=staff_headers,
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_generate_medical_record_pdf(client: AsyncClient, test_db: AsyncSession):
    """Test PDF generation for medical record."""
    # Setup: Create patient with medical record and entries
    allowed_repo = AllowedPersonRepository(test_db)
    await allowed_repo.bulk_create([{"dni": "12345678901"}])
    
    register_response = await client.post(
        "/auth/users/register",
        json={
            "dni": "12345678901",
            "password": "testpassword123",
            "full_name": "Test Patient",
            "role": "patient",
        },
    )
    patient_id = register_response.json()["id"]
    
    # Create medical record with data
    medical_record_repo = MedicalRecordRepository(test_db)
    medical_record = await medical_record_repo.create(
        patient_id=patient_id,
        registration_survey={"allergies": "None", "chronic_diseases": ["Diabetes"]}
    )
    
    # Add an entry
    await medical_record_repo.add_entry(
        patient_id=patient_id,
        entry={
            "entry_type": "consultation",
            "specialty": "Cardiology",
            "diagnosis": "Hypertension"
        }
    )
    
    # Create auth token for patient
    token = create_access_token({"sub": "12345678901", "role": "patient"})
    headers = {"Authorization": f"Bearer {token}"}
    
    # Generate PDF
    response = await client.get(f"/patients/{patient_id}/medical-record/pdf", headers=headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "content-disposition" in response.headers
    assert f"historia_clinica_{patient_id}.pdf" in response.headers["content-disposition"]
    # Verify we got PDF content
    assert len(response.content) > 0
    # PDF files start with %PDF
    assert response.content[:4] == b'%PDF'
