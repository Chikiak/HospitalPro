import pytest
from httpx import AsyncClient

from app.core.security import create_access_token
from app.repositories.allowed_person_repository import AllowedPersonRepository
from app.repositories.medical_record_repository import MedicalRecordRepository


@pytest.mark.asyncio
async def test_pdf_medical_record_legacy_non_dict_registration_survey(
    client: AsyncClient, test_db
):
    """Un registro legacy con registration_survey no-dict no debe romper el PDF.

    La columna JSON de registration_survey puede albergar valores legacy
    (string, número, lista) que no son dict. generate_medical_record_pdf
    llamaba survey.items() sin comprobar el tipo y el endpoint
    GET /patients/{id}/medical-record/pdf devolvía 500, impidiendo al
    paciente (o al personal) descargar su historia clínica.
    """
    await AllowedPersonRepository(test_db).bulk_create([{"dni": "32323232302"}])

    register_response = await client.post(
        "/auth/users/register",
        json={
            "dni": "32323232302",
            "password": "testpassword123",
            "full_name": "Paciente Legacy",
            "role": "patient",
        },
    )
    assert register_response.status_code == 201, register_response.text
    patient_id = register_response.json()["id"]

    medical_record_repo = MedicalRecordRepository(test_db)
    await medical_record_repo.create(
        patient_id=patient_id,
        registration_survey="texto plano de registro legacy",  # valor legacy no-dict
    )

    token = create_access_token({"sub": "32323232302", "role": "patient"})
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get(
        f"/patients/{patient_id}/medical-record/pdf", headers=headers
    )
    assert response.status_code == 200, response.text
    assert response.headers["content-type"] == "application/pdf"
    assert "content-disposition" in response.headers
    assert f"historia_clinica_{patient_id}.pdf" in response.headers["content-disposition"]
    assert response.content.startswith(b"%PDF")
    assert len(response.content) > 0
