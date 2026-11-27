"""Tests for F2-06: generic server errors must not leak internal details.

These tests inject exceptions that carry sensitive markers (passwords, DSN,
SQL, stack traces) and verify that:
- the client-facing response never contains those markers nor SQL/stack/DSN,
- the HTTP status is a generic 500/503 with a generic message,
- server-side logging keeps the diagnostic (exception type) without
  credentials: markers must not appear in ANY log output
  (caplog.text nor any rec.exc_info traceback, causes included).

Covered areas: patients (medical history), the Oracle adapter, and the
generic catch-all middleware in app.main.
"""
import logging
import traceback
from unittest.mock import patch

import oracledb
import pytest
from httpx import AsyncClient

from app.adapters.oracle_adapter import OracleAdapter
from app.core.security import create_access_token
from app.exceptions import ServiceUnavailable
from app.models.user import User, UserRole
from app.repositories.triage_repository import TriageRepository

# Synthetic test markers (obviously fake, never real credentials). They are
# injected into exceptions and asserted to never reach the client or the log.
SENSITIVE_PASSWORD_MARKER = "__F206_TEST_PASSWORD_MARKER__"
SENSITIVE_DSN_MARKER = "__F206_TEST_DSN_MARKER__"
SENSITIVE_SQL_MARKER = "__F206_TEST_SQL_MARKER__"

ALL_MARKERS = (
    SENSITIVE_PASSWORD_MARKER,
    SENSITIVE_DSN_MARKER,
    SENSITIVE_SQL_MARKER,
)

MARKERS_AND_STACK = ALL_MARKERS + ("Traceback", "stack")


def _assert_no_marker_in_log_output(caplog, extra=()):
    """Markers must not appear in any log output: caplog.text nor any
    record's exc_info traceback (causes included)."""
    text = caplog.text
    for marker in ALL_MARKERS + extra:
        assert marker not in text, f"marker leaked into caplog.text: {marker!r}"

    for rec in caplog.records:
        if rec.exc_info is not None:
            formatted = "".join(traceback.format_exception(*rec.exc_info))
            for marker in ALL_MARKERS + extra:
                assert marker not in formatted, (
                    f"marker leaked into record traceback: {marker!r}"
                )


@pytest.mark.asyncio
async def test_update_medical_history_500_hides_sensitive_markers(
    client: AsyncClient,
    test_db,
    make_token,
    caplog,
):
    """A 500 from update_medical_history must hide the exception detail."""
    patient = User(
        dni="55555555555",
        hashed_password="hashed",
        full_name="Sensitive Patient",
        role=UserRole.PATIENT,
        is_active=True,
    )
    test_db.add(patient)
    await test_db.flush()
    patient_id = patient.id

    token = create_access_token({"sub": "55555555555", "role": "patient"})
    headers = {"Authorization": f"Bearer {token}"}

    sensitive_msg = (
        f"boom {SENSITIVE_PASSWORD_MARKER} {SENSITIVE_DSN_MARKER} "
        f"{SENSITIVE_SQL_MARKER} dni='x'"
    )

    with patch.object(
        TriageRepository,
        "get_by_patient_id",
        side_effect=Exception(sensitive_msg),
    ):
        caplog.set_level(logging.ERROR, logger="app.main")
        response = await client.patch(
            f"/patients/{patient_id}/medical-history",
            json={"medical_history": {"chronic_diseases": "x"}},
            headers=headers,
        )

    assert response.status_code == 500
    detail = response.json()["detail"]
    assert detail == "Error interno del servidor"
    for marker in MARKERS_AND_STACK:
        assert marker not in detail, f"marker leaked into 500 detail: {marker!r}"

    # Server-side log: diagnostic present (type), no markers anywhere.
    messages = [rec.getMessage() for rec in caplog.records]
    assert any("Unhandled server error" in m for m in messages)
    assert any("Exception" in m for m in messages), "diagnostic (exception type) missing"
    _assert_no_marker_in_log_output(caplog, extra=MARKERS_AND_STACK[3:])


@pytest.mark.asyncio
async def test_update_medical_history_503_service_unavailable_hides_markers(
    client: AsyncClient,
    test_db,
    make_token,
    caplog,
):
    """A ServiceUnavailable from the Oracle adapter path becomes a generic 503."""
    patient = User(
        dni="55555555556",
        hashed_password="hashed",
        full_name="Oracle Patient",
        role=UserRole.PATIENT,
        is_active=True,
    )
    test_db.add(patient)
    await test_db.flush()
    patient_id = patient.id

    token = create_access_token({"sub": "55555555556", "role": "patient"})
    headers = {"Authorization": f"Bearer {token}"}

    with patch.object(
        TriageRepository,
        "get_by_patient_id",
        side_effect=ServiceUnavailable(
            f"internal: {SENSITIVE_PASSWORD_MARKER} {SENSITIVE_DSN_MARKER}"
        ),
    ):
        caplog.set_level(logging.ERROR, logger="app.main")
        response = await client.patch(
            f"/patients/{patient_id}/medical-history",
            json={"medical_history": {"chronic_diseases": "x"}},
            headers=headers,
        )

    assert response.status_code == 503
    detail = response.json()["detail"]
    assert detail == "Servicio temporalmente no disponible"
    for marker in ALL_MARKERS + ("Traceback",):
        assert marker not in detail, f"marker leaked into 503 detail: {marker!r}"

    messages = [rec.getMessage() for rec in caplog.records]
    assert any("External service unavailable" in m for m in messages)
    assert any("ServiceUnavailable" in m for m in messages), "diagnostic (exception type) missing"
    _assert_no_marker_in_log_output(caplog)


def test_oracle_adapter_hides_dsn_and_password():
    """ServiceUnavailable raised by the adapter must not embed the driver error."""
    adapter = OracleAdapter(
        user="legacy_user",
        password=SENSITIVE_PASSWORD_MARKER,
        dsn=SENSITIVE_DSN_MARKER,
    )
    driver_msg = (
        f"ORA-12514: TNS:listener does not know service "
        f"(user=legacy_user password={SENSITIVE_PASSWORD_MARKER} "
        f"dsn={SENSITIVE_DSN_MARKER})"
    )
    with patch(
        "app.adapters.oracle_adapter.oracledb.connect",
        side_effect=oracledb.Error(driver_msg),
    ):
        with pytest.raises(ServiceUnavailable) as excinfo:
            adapter.get_patient_history("12345678")

    msg = str(excinfo.value)
    assert msg == "No se pudo conectar al servicio de historial de pacientes"
    for marker in ALL_MARKERS + ("ORA-12514", "Traceback"):
        assert marker not in msg, f"marker leaked into ServiceUnavailable: {marker!r}"


@pytest.mark.asyncio
async def test_http_error_4xx_still_works(client: AsyncClient, test_db, make_token):
    """Functional HTTP errors (4xx) keep their status and detail (not 500)."""
    patient = User(
        dni="55555555557",
        hashed_password="hashed",
        full_name="No History Patient",
        role=UserRole.PATIENT,
        is_active=True,
    )
    test_db.add(patient)
    await test_db.flush()
    patient_id = patient.id

    token = create_access_token({"sub": "55555555557", "role": "patient"})
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get(
        f"/patients/{patient_id}/medical-record", headers=headers
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "No se encontró historia clínica para este paciente"
