"""Regresión: export de cita con historial médico legacy (medical_history no-dict).

El endpoint GET /appointments/{id}/export asume que triage.medical_history es
un dict y llama .get() sobre él. Cuando un registro legacy almacena
medical_history como string/número/lista, .get() lanza AttributeError y el
endpoint devolve 500 en lugar de la hoja Excel. Los campos afectados deben
degradarse a "No registrado" sin romper la exportación.
"""
from datetime import datetime, timedelta
from io import BytesIO

import pytest
from httpx import AsyncClient
from openpyxl import load_workbook
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.appointment import Appointment, AppointmentStatus
from app.models.user import User, UserRole
from app.repositories.allowed_person_repository import AllowedPersonRepository
from app.repositories.triage_repository import TriageRepository


def _read_excel_fields(content: bytes) -> dict[str, object]:
    """Lee la hoja 'Información del Paciente' y devuelve {campo: valor} desde la fila 2."""
    workbook = load_workbook(BytesIO(content), data_only=True)
    sheet = workbook["Información del Paciente"]
    fields: dict[str, object] = {}
    for row in sheet.iter_rows(min_row=2, values_only=True):
        if row[0] is None:
            continue
        fields[row[0]] = row[1]
    return fields


async def _create_staff(test_db: AsyncSession, dni: str) -> str:
    test_db.add(
        User(dni=dni, hashed_password="hashed", full_name="Staff User", role=UserRole.STAFF, is_active=True)
    )
    await test_db.commit()
    return create_access_token({"sub": dni, "role": "staff"})


async def _create_patient(client: AsyncClient, test_db: AsyncSession, dni: str) -> int:
    allowed_repo = AllowedPersonRepository(test_db)
    await allowed_repo.bulk_create([{"dni": dni}])
    reg = await client.post(
        "/auth/users/register",
        json={
            "dni": dni,
            "password": "testpassword123",
            "full_name": "Paciente Test",
            "role": "patient",
        },
    )
    assert reg.status_code == 201, reg.text
    return reg.json()["id"]


async def _create_appointment(test_db: AsyncSession, patient_id: int) -> int:
    appt = Appointment(
        patient_id=patient_id,
        appointment_date=datetime.now() + timedelta(days=7),
        specialty="Cardiologia",
        status=AppointmentStatus.SCHEDULED,
    )
    test_db.add(appt)
    await test_db.commit()
    await test_db.refresh(appt)
    return appt.id


@pytest.mark.asyncio
@pytest.mark.parametrize("idx,legacy_value", [(1, "texto legacy no es un dict"), (2, 12345), (3, ["Penicilina"])])
async def test_export_with_legacy_non_dict_medical_history_200(
    client: AsyncClient, test_db: AsyncSession, idx: int, legacy_value: object
):
    """medical_history como string legacy: export devuelve 200 y campos sin datos."""
    staff_dni = f"91000000{idx}01"
    patient_dni = f"91000000{idx}02"
    staff_token = await _create_staff(test_db, staff_dni)
    patient_id = await _create_patient(client, test_db, patient_dni)
    appt_id = await _create_appointment(test_db, patient_id)

    triage_repo = TriageRepository(test_db)
    await triage_repo.create(
        patient_id=patient_id,
        medical_history=legacy_value,
        allergies="Penicilina",
    )
    await test_db.commit()

    headers = {"Authorization": f"Bearer {staff_token}"}
    response = await client.get(f"/appointments/{appt_id}/export", headers=headers)

    assert response.status_code == 200, response.text
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert "attachment;" in response.headers["content-disposition"]
    assert len(response.content) > 0

    fields = _read_excel_fields(response.content)
    assert fields["Enfermedades Crónicas"] == "No registrado"
    assert fields["Alergias a Medicamentos"] == "Penicilina"
    assert fields["Otra Información"] == "No registrado"


@pytest.mark.asyncio
async def test_export_with_dict_medical_history_still_works(
    client: AsyncClient, test_db: AsyncSession
):
    """medical_history dict válido: export devuelve 200 con los datos (no regresión)."""
    staff_token = await _create_staff(test_db, "92000000001")
    patient_id = await _create_patient(client, test_db, "92000000002")
    appt_id = await _create_appointment(test_db, patient_id)

    triage_repo = TriageRepository(test_db)
    await triage_repo.create(
        patient_id=patient_id,
        medical_history={
            "chronic_diseases": "Diabetes",
            "medication_allergies": ["Penicilina"],
            "other_information": "Control cada 6 meses",
        },
        allergies="Penicilina",
    )
    await test_db.commit()

    headers = {"Authorization": f"Bearer {staff_token}"}
    response = await client.get(f"/appointments/{appt_id}/export", headers=headers)

    assert response.status_code == 200, response.text
    assert len(response.content) > 0

    fields = _read_excel_fields(response.content)
    assert fields["Enfermedades Crónicas"] == "Diabetes"
    assert fields["Alergias a Medicamentos"] == "Penicilina"
    assert fields["Otra Información"] == "Control cada 6 meses"


@pytest.mark.asyncio
async def test_export_with_null_medical_history_200(
    client: AsyncClient, test_db: AsyncSession
):
    """medical_history None: export devuelve 200 y campos 'No registrado'."""
    staff_token = await _create_staff(test_db, "93000000001")
    patient_id = await _create_patient(client, test_db, "93000000002")
    appt_id = await _create_appointment(test_db, patient_id)

    triage_repo = TriageRepository(test_db)
    await triage_repo.create(patient_id=patient_id, medical_history=None, allergies=None)
    await test_db.commit()

    headers = {"Authorization": f"Bearer {staff_token}"}
    response = await client.get(f"/appointments/{appt_id}/export", headers=headers)

    assert response.status_code == 200, response.text
    assert len(response.content) > 0

    fields = _read_excel_fields(response.content)
    assert fields["Enfermedades Crónicas"] == "No registrado"
    assert fields["Alergias a Medicamentos"] == "No registrado"
    assert fields["Otra Información"] == "No registrado"
