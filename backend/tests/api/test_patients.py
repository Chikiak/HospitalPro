import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.user import User, UserRole
from app.repositories.allowed_person_repository import AllowedPersonRepository


@pytest.mark.asyncio
async def test_list_all_patients_empty(client: AsyncClient, test_db: AsyncSession):
    """Test listing patients when database is empty."""
    # Create staff user directly in DB (not via public registration)
    test_db.add(
        User(
            dni="99999999999",
            hashed_password="hashed",
            full_name="Staff User",
            role=UserRole.STAFF,
            is_active=True,
        )
    )
    await test_db.commit()
    
    # Create token for staff
    token = create_access_token({"sub": "99999999999", "role": "staff"})
    headers = {"Authorization": f"Bearer {token}"}
    
    response = await client.get("/patients/", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


@pytest.mark.asyncio
async def test_list_all_patients_with_data(client: AsyncClient, test_db: AsyncSession):
    """Test listing patients with patient data."""
    # Create staff user directly in DB (not via public registration)
    test_db.add(
        User(
            dni="99999999999",
            hashed_password="hashed",
            full_name="Staff User",
            role=UserRole.STAFF,
            is_active=True,
        )
    )
    await test_db.commit()
    
    # Add patient DNI to allowed persons list
    allowed_repo = AllowedPersonRepository(test_db)
    await allowed_repo.bulk_create([{"dni": "98765432101"}])
    
    # Create a patient user via public registration
    patient_response = await client.post(
        "/auth/users/register",
        json={
            "dni": "98765432101",
            "password": "testpassword123",
            "full_name": "Test Patient",
            "role": "patient",
        },
    )
    assert patient_response.status_code == 201
    patient = patient_response.json()
    patient_id = patient["id"]
    
    # Create token for staff to add medical history
    staff_token = create_access_token({"sub": "99999999999", "role": "staff"})
    staff_headers = {"Authorization": f"Bearer {staff_token}"}
    
    # Add medical history for the patient
    await client.patch(
        f"/patients/{patient_id}/medical-history",
        json={
            "medical_history": {
                "chronic_diseases": "Diabetes",
                "current_medications": "Metformin"
            },
            "allergies": "Penicillin"
        },
        headers=staff_headers,
    )
    
    # List all patients
    response = await client.get("/patients/", headers=staff_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    
    # Find our test patient
    test_patient = next((p for p in data if p["dni"] == "98765432101"), None)
    assert test_patient is not None
    assert test_patient["full_name"] == "Test Patient"
    assert test_patient["allergies"] == "Penicillin"
    assert test_patient["medical_history"]["chronic_diseases"] == "Diabetes"


@pytest.mark.asyncio
async def test_list_patients_excludes_non_patients(client: AsyncClient, test_db: AsyncSession):
    """Test that listing patients only returns users with patient role."""
    # Create staff user directly in DB (not via public registration)
    test_db.add(
        User(
            dni="99999999999",
            hashed_password="hashed",
            full_name="Staff User",
            role=UserRole.STAFF,
            is_active=True,
        )
    )
    await test_db.commit()
    
    # Create a patient
    allowed_repo = AllowedPersonRepository(test_db)
    await allowed_repo.bulk_create([{"dni": "11111111111"}])
    
    await client.post(
        "/auth/users/register",
        json={
            "dni": "11111111111",
            "password": "testpassword123",
            "full_name": "Patient User",
            "role": "patient",
        },
    )
    
    # Create a doctor directly in DB (not via public registration)
    test_db.add(
        User(
            dni="22222222222",
            hashed_password="hashed",
            full_name="Doctor User",
            role=UserRole.DOCTOR,
            is_active=True,
        )
    )
    await test_db.commit()
    
    # Create token for staff
    token = create_access_token({"sub": "99999999999", "role": "staff"})
    headers = {"Authorization": f"Bearer {token}"}
    
    # List all patients
    response = await client.get("/patients/", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    
    # Check that only patient role users are returned
    patient_dnis = [p["dni"] for p in data]
    assert "11111111111" in patient_dnis
    assert "22222222222" not in patient_dnis


@pytest.mark.asyncio
async def test_list_patients_without_medical_history(client: AsyncClient, test_db: AsyncSession):
    """Test listing patients who haven't filled medical history yet."""
    # Create staff user directly in DB (not via public registration)
    test_db.add(
        User(
            dni="99999999999",
            hashed_password="hashed",
            full_name="Staff User",
            role=UserRole.STAFF,
            is_active=True,
        )
    )
    await test_db.commit()
    
    # Create a patient without medical history
    allowed_repo = AllowedPersonRepository(test_db)
    await allowed_repo.bulk_create([{"dni": "33333333333"}])
    
    patient_response = await client.post(
        "/auth/users/register",
        json={
            "dni": "33333333333",
            "password": "testpassword123",
            "full_name": "New Patient",
            "role": "patient",
        },
    )
    assert patient_response.status_code == 201
    
    # Create token for staff
    token = create_access_token({"sub": "99999999999", "role": "staff"})
    headers = {"Authorization": f"Bearer {token}"}
    
    # List all patients
    response = await client.get("/patients/", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    
    # Find our test patient
    test_patient = next((p for p in data if p["dni"] == "33333333333"), None)
    assert test_patient is not None
    assert test_patient["full_name"] == "New Patient"
    assert test_patient["medical_history"] is None
    assert test_patient["allergies"] is None


@pytest.mark.asyncio
async def test_update_allergies_preserves_medical_history(client: AsyncClient, test_db: AsyncSession):
    """Regression: updating only allergies must not erase existing medical_history."""
    # Staff user
    test_db.add(
        User(
            dni="99999999999",
            hashed_password="hashed",
            full_name="Staff User",
            role=UserRole.STAFF,
            is_active=True,
        )
    )
    await test_db.commit()

    # Allowed person + patient
    allowed_repo = AllowedPersonRepository(test_db)
    await allowed_repo.bulk_create([{"dni": "55555555555"}])

    patient_response = await client.post(
        "/auth/users/register",
        json={
            "dni": "55555555555",
            "password": "testpassword123",
            "full_name": "Test Patient",
            "role": "patient",
        },
    )
    assert patient_response.status_code == 201
    patient_id = patient_response.json()["id"]

    # Seed medical history via staff
    staff_token = create_access_token({"sub": "99999999999", "role": "staff"})
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    seed_response = await client.patch(
        f"/patients/{patient_id}/medical-history",
        json={
            "medical_history": {
                "chronic_diseases": "Diabetes",
                "current_medications": "Metformin",
            },
            "allergies": "Penicillin",
        },
        headers=staff_headers,
    )
    assert seed_response.status_code == 200

    # Update ONLY allergies (no medical_history key in payload)
    update_response = await client.patch(
        f"/patients/{patient_id}/medical-history",
        json={"allergies": "Sulfonamides"},
        headers=staff_headers,
    )
    assert update_response.status_code == 200
    update_data = update_response.json()
    assert update_data["allergies"] == "Sulfonamides"
    assert update_data["medical_history"] is not None
    assert update_data["medical_history"]["chronic_diseases"] == "Diabetes"
    assert update_data["medical_history"]["current_medications"] == "Metformin"

    # medical_history must be preserved
    response = await client.get(
        f"/patients/{patient_id}/medical-history", headers=staff_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["allergies"] == "Sulfonamides"
    assert data["medical_history"] is not None
    assert data["medical_history"]["chronic_diseases"] == "Diabetes"
    assert data["medical_history"]["current_medications"] == "Metformin"


@pytest.mark.asyncio
async def test_update_allergies_with_empty_medical_history_preserves_existing(
    client: AsyncClient, test_db: AsyncSession
):
    """Regression: PATCH with medical_history={} must not erase existing history.

    Covers the branch ``if not medical_history: medical_history = None``: an empty
    object is normalized to None and the repository leaves the stored value intact.
    """
    # Staff user
    test_db.add(
        User(
            dni="99999999999",
            hashed_password="hashed",
            full_name="Staff User",
            role=UserRole.STAFF,
            is_active=True,
        )
    )
    await test_db.commit()

    # Allowed person + patient
    allowed_repo = AllowedPersonRepository(test_db)
    await allowed_repo.bulk_create([{"dni": "66666666666"}])

    patient_response = await client.post(
        "/auth/users/register",
        json={
            "dni": "66666666666",
            "password": "testpassword123",
            "full_name": "Test Patient",
            "role": "patient",
        },
    )
    assert patient_response.status_code == 201
    patient_id = patient_response.json()["id"]

    # Seed medical history + allergies via staff
    staff_token = create_access_token({"sub": "99999999999", "role": "staff"})
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    seed_response = await client.patch(
        f"/patients/{patient_id}/medical-history",
        json={
            "medical_history": {
                "chronic_diseases": "Diabetes",
                "current_medications": "Metformin",
            },
            "allergies": "Penicillin",
        },
        headers=staff_headers,
    )
    assert seed_response.status_code == 200

    # Update allergies with an empty medical_history object
    update_response = await client.patch(
        f"/patients/{patient_id}/medical-history",
        json={"medical_history": {}, "allergies": "Latex"},
        headers=staff_headers,
    )
    assert update_response.status_code == 200
    update_data = update_response.json()
    assert update_data["allergies"] == "Latex"
    assert update_data["medical_history"] is not None
    assert update_data["medical_history"]["chronic_diseases"] == "Diabetes"
    assert update_data["medical_history"]["current_medications"] == "Metformin"

    # Confirmed by a subsequent GET
    response = await client.get(
        f"/patients/{patient_id}/medical-history", headers=staff_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["allergies"] == "Latex"
    assert data["medical_history"] is not None
    assert data["medical_history"]["chronic_diseases"] == "Diabetes"
    assert data["medical_history"]["current_medications"] == "Metformin"
