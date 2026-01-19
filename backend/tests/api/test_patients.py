import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_all_patients_empty(client: AsyncClient):
    """Test listing patients when database is empty."""
    response = await client.get("/patients/")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


@pytest.mark.asyncio
async def test_list_all_patients_with_data(client: AsyncClient):
    """Test listing patients with patient data."""
    # Create a patient user first
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
    )
    
    # List all patients
    response = await client.get("/patients/")
    
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
async def test_list_patients_excludes_non_patients(client: AsyncClient):
    """Test that listing patients only returns users with patient role."""
    # Create a patient
    await client.post(
        "/auth/users/register",
        json={
            "dni": "11111111111",
            "password": "testpassword123",
            "full_name": "Patient User",
            "role": "patient",
        },
    )
    
    # Create a doctor (non-patient role)
    await client.post(
        "/auth/users/register",
        json={
            "dni": "22222222222",
            "password": "testpassword123",
            "full_name": "Doctor User",
            "role": "doctor",
        },
    )
    
    # List all patients
    response = await client.get("/patients/")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check that only patient role users are returned
    patient_dnis = [p["dni"] for p in data]
    assert "11111111111" in patient_dnis
    assert "22222222222" not in patient_dnis


@pytest.mark.asyncio
async def test_list_patients_without_medical_history(client: AsyncClient):
    """Test listing patients who haven't filled medical history yet."""
    # Create a patient without medical history
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
    
    # List all patients
    response = await client.get("/patients/")
    
    assert response.status_code == 200
    data = response.json()
    
    # Find our test patient
    test_patient = next((p for p in data if p["dni"] == "33333333333"), None)
    assert test_patient is not None
    assert test_patient["full_name"] == "New Patient"
    assert test_patient["medical_history"] is None
    assert test_patient["allergies"] is None
