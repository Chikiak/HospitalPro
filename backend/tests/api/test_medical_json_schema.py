"""Tests for F2-09: Validar estructura JSON del historial médico.

Cobertura:
- Claves desconocidas en medical_history / entries -> 422, sin escritura.
- Tipos invalidos -> 422, sin escritura.
- Exceso de tamaño -> 422, sin escritura.
- Datos validos completos -> 200 y round-trip (escribir y leer devuelve lo mismo).
- Lectura de registros legacy (JSON arbitrario ya almacenado) -> 200, sin fallar al leer.
- F2-06: errores internos siguen siendo genéricos (ver tests/api/test_generic_server_errors.py).
"""
from unittest.mock import patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.models.user import User, UserRole
from app.repositories.allowed_person_repository import AllowedPersonRepository
from app.repositories.medical_record_repository import MedicalRecordRepository
from app.repositories.triage_repository import TriageRepository
from app.repositories.user_repository import UserRepository


async def _create_patient(client: AsyncClient, test_db: AsyncSession, dni: str):
    """Crea un paciente (allowed person + registro) y devuelve (patient_id, headers)."""
    allowed_repo = AllowedPersonRepository(test_db)
    await allowed_repo.bulk_create([{"dni": dni, "full_name": "Paciente Test"}])

    reg = await client.post(
        "/auth/users/register",
        json={
            "dni": dni,
            "password": "testpassword123",
            "full_name": "Paciente Test",
            "role": "patient",
        },
    )
    assert reg.status_code == 201
    patient_id = reg.json()["id"]

    token = create_access_token({"sub": dni, "role": "patient"})
    headers = {"Authorization": f"Bearer {token}"}
    return patient_id, headers


async def _create_patient_with_record(client: AsyncClient, test_db: AsyncSession, dni: str):
    """Crea paciente con historial medico y devuelve (patient_id, staff_headers)."""
    patient_id, patient_headers = await _create_patient(client, test_db, dni)

    # Crear usuario staff con token para agregar entradas.
    allowed_repo = AllowedPersonRepository(test_db)
    await allowed_repo.bulk_create([{"dni": "80000000000", "full_name": "Staff Test"}])
    user_repo = UserRepository(test_db)
    staff_user = await user_repo.create(
        dni="80000000000",
        hashed_password=get_password_hash("staffpassword123"),
        full_name="Staff Test",
        role=UserRole.STAFF,
    )
    await test_db.commit()
    staff_token = create_access_token({"sub": staff_user.dni, "role": "staff"})
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    # Crear historial medico para el paciente.
    medical_record_repo = MedicalRecordRepository(test_db)
    await medical_record_repo.create(
        patient_id=patient_id,
        registration_survey={"chronic_diseases": "Diabetes"},
    )

    return patient_id, staff_headers


@pytest.mark.asyncio
async def test_medical_history_rejects_unknown_key(client, test_db):
    """Una clave desconocida en medical_history debe dar 422 y no escribir."""
    patient_id, headers = await _create_patient(client, test_db, "70000000001")

    response = await client.patch(
        f"/patients/{patient_id}/medical-history",
        json={
            "medical_history": {
                "chronic_diseases": "Diabetes",
                "campo_inexistente": "debería rechazarse",
            }
        },
        headers=headers,
    )
    assert response.status_code == 422, response.text

    # Nada se escribió: el historial sigue vacío/nulo.
    get_resp = await client.get(
        f"/patients/{patient_id}/medical-history", headers=headers
    )
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_medical_history_rejects_invalid_type(client, test_db):
    """Un tipo invalido (chronic_diseases como int) debe dar 422."""
    patient_id, headers = await _create_patient(client, test_db, "70000000002")

    response = await client.patch(
        f"/patients/{patient_id}/medical-history",
        json={"medical_history": {"chronic_diseases": 12345}},
        headers=headers,
    )
    assert response.status_code == 422, response.text


@pytest.mark.asyncio
async def test_medical_history_rejects_oversized(client, test_db):
    """Un medical_history demasiado grande debe dar 422."""
    patient_id, headers = await _create_patient(client, test_db, "70000000003")

    big = "x" * 20000  # supera el limite de 10 000 caracteres del historial
    response = await client.patch(
        f"/patients/{patient_id}/medical-history",
        json={"medical_history": {"other_information": big}},
        headers=headers,
    )
    assert response.status_code == 422, response.text


@pytest.mark.asyncio
async def test_medical_history_valid_complete_round_trip(client, test_db):
    """Datos validos completos se escriben y se leen igual (round-trip)."""
    patient_id, headers = await _create_patient(client, test_db, "70000000004")

    payload = {
        "medical_history": {
            "chronic_diseases": ["Diabetes", "Hipertension"],
            "medication_allergies": ["Penicilina"],
            "other_information": "Sin cirugias previas.",
            "previous_surgeries": "Ninguna",
            "current_medications": "Metformina 500 mg",
            "family_history": "Diabetes (padre)",
            "habits": "No fuma",
            "other_medical_info": "Controles periodicos",
            "allergies": "Polen",
        },
        "allergies": "Penicilina, Polen",
    }

    response = await client.patch(
        f"/patients/{patient_id}/medical-history",
        json=payload,
        headers=headers,
    )
    assert response.status_code == 200, response.text

    # Round-trip: leer y verificar que se devuelve lo escrito.
    get_resp = await client.get(
        f"/patients/{patient_id}/medical-history", headers=headers
    )
    assert get_resp.status_code == 200
    data = get_resp.json()
    mh = data["medical_history"]
    assert mh["chronic_diseases"] == ["Diabetes", "Hipertension"]
    assert mh["medication_allergies"] == ["Penicilina"]
    assert mh["other_information"] == "Sin cirugias previas."
    assert data["allergies"] == "Penicilina, Polen"


@pytest.mark.asyncio
async def test_medical_history_legacy_read(client, test_db):
    """Un registro legacy con JSON arbitrario (claves desconocidas) se lee sin fallar."""
    patient_id, headers = await _create_patient(client, test_db, "70000000005")

    # Escribir directamente en la DB (saltea la validacion de escritura), simulando un
    # registro legacy ya almacenado con claves fuera del esquema actual.
    triage_repo = TriageRepository(test_db)
    await triage_repo.create(
        patient_id=patient_id,
        medical_history={
            "legacy_key_1": "valor-antiguo",
            "legacy_key_2": 42,
            "legacy_key_3": {"anidado": True},
            "chronic_diseases": "Diabetes",
        },
        allergies="Polvo",
    )

    get_resp = await client.get(
        f"/patients/{patient_id}/medical-history", headers=headers
    )
    assert get_resp.status_code == 200, get_resp.text
    data = get_resp.json()
    assert data["medical_history"]["legacy_key_1"] == "valor-antiguo"
    assert data["medical_history"]["legacy_key_2"] == 42
    assert data["medical_history"]["legacy_key_3"] == {"anidado": True}
    assert data["allergies"] == "Polvo"


@pytest.mark.asyncio
async def test_medical_record_entry_rejects_unknown_key(client, test_db):
    """Una entrada con clave desconocida debe dar 422."""
    patient_id, staff_headers = await _create_patient_with_record(
        client, test_db, "70000000006"
    )

    response = await client.post(
        f"/patients/{patient_id}/medical-record/entries",
        json={
            "entry_type": "consultation",
            "specialty": "Cardiologia",
            "clave_inexistente": "debería rechazarse",
        },
        headers=staff_headers,
    )
    assert response.status_code == 422, response.text


@pytest.mark.asyncio
async def test_medical_record_entry_rejects_invalid_entry_type(client, test_db):
    """entry_type invalido debe dar 422."""
    patient_id, staff_headers = await _create_patient_with_record(
        client, test_db, "70000000007"
    )

    response = await client.post(
        f"/patients/{patient_id}/medical-record/entries",
        json={
            "entry_type": "rayos_x",  # no es 'consultation' ni 'lab_result'
            "specialty": "Radiologia",
        },
        headers=staff_headers,
    )
    assert response.status_code == 422, response.text


@pytest.mark.asyncio
async def test_medical_record_entry_rejects_oversized_results(client, test_db):
    """results demasiado grande debe dar 422."""
    patient_id, staff_headers = await _create_patient_with_record(
        client, test_db, "70000000008"
    )

    big_results = {"campo": "x" * 6000}  # supera el limite de 5000 de results
    response = await client.post(
        f"/patients/{patient_id}/medical-record/entries",
        json={
            "entry_type": "lab_result",
            "results": big_results,
        },
        headers=staff_headers,
    )
    assert response.status_code == 422, response.text


@pytest.mark.asyncio
async def test_medical_record_entry_valid_round_trip(client, test_db):
    """Una entrada valida se escribe y se lee igual (round-trip)."""
    patient_id, staff_headers = await _create_patient_with_record(
        client, test_db, "70000000009"
    )

    entry = {
        "entry_type": "lab_result",
        "specialty": "Laboratorio",
        "doctor_name": "Dra. Lopez",
        "diagnosis": "Glucemia alta",
        "notes": "Control en un mes",
        "results": {"glucosa": "140 mg/dL", "hba1c": "7.2%"},
    }

    response = await client.post(
        f"/patients/{patient_id}/medical-record/entries",
        json=entry,
        headers=staff_headers,
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data["entries"]) == 1
    e = data["entries"][0]
    assert e["entry_type"] == "lab_result"
    assert e["specialty"] == "Laboratorio"
    assert e["results"]["glucosa"] == "140 mg/dL"
    assert "timestamp" in e


@pytest.mark.asyncio
async def test_f206_generic_errors_still_generic(client, test_db):
    """F2-06: los errores internos siguen siendo genericos (no filtran detalles)."""
    patient = User(
        dni="70000000099",
        hashed_password="hashed",
        full_name="F206 Patient",
        role=UserRole.PATIENT,
        is_active=True,
    )
    test_db.add(patient)
    await test_db.flush()
    patient_id = patient.id
    token = create_access_token({"sub": "70000000099", "role": "patient"})
    headers = {"Authorization": f"Bearer {token}"}

    from app.repositories.triage_repository import TriageRepository

    with patch.object(
        TriageRepository, "get_by_patient_id", side_effect=Exception("boom secreto")
    ):
        response = await client.patch(
            f"/patients/{patient_id}/medical-history",
            json={"medical_history": {"chronic_diseases": "x"}},
            headers=headers,
        )
    assert response.status_code == 500
    assert response.json()["detail"] == "Error interno del servidor"
