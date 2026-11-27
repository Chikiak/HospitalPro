"""Tests para la política centralizada de contraseñas (F2-08).

Cubre la regla reutilizable de longitud mínima (8 caracteres) y la aplica
paramétricamente a todos los esquemas de creación y cambio de contraseña:
PatientCreate, UserCreate, StaffPasswordUpdateRequest y AdminVerifyRequest.
"""
import pytest
from pydantic import ValidationError

from app.core.password_policy import MIN_PASSWORD_LENGTH, validate_min_password_length
from app.schemas.patient import PatientCreate
from app.schemas.security import AdminVerifyRequest, StaffPasswordUpdateRequest
from app.schemas.user import UserCreate

SHORT_PASSWORDS = ["", "a", "1234567", "short1", "aaaaaaa"]  # siempre < 8
VALID_PASSWORDS = ["aaaaaaaa", "a" * 9, "securepass123"]  # 8 o más


class TestPasswordMinLengthCentralRule:
    """La regla central es la única fuente de la longitud mínima."""

    @pytest.mark.parametrize("password", VALID_PASSWORDS)
    def test_accepts_eight_or_more_characters(self, password):
        assert validate_min_password_length(password) == password

    @pytest.mark.parametrize("password", SHORT_PASSWORDS)
    def test_rejects_less_than_eight_characters(self, password):
        with pytest.raises(ValueError, match=f"al menos {MIN_PASSWORD_LENGTH}"):
            validate_min_password_length(password)

    def test_rejects_non_string_value(self):
        with pytest.raises(ValueError, match=f"al menos {MIN_PASSWORD_LENGTH}"):
            validate_min_password_length(12345)


class TestPatientCreateEnforcesMinPassword:
    """PatientCreate pasó de 6 a 8 caracteres (F2-08): no se debilita, se unifica."""

    @pytest.mark.parametrize("password", SHORT_PASSWORDS)
    def test_rejects_short_password(self, password):
        data = {"dni": "12345678901", "full_name": "Jane Doe", "password": password}
        with pytest.raises(ValidationError) as exc_info:
            PatientCreate(**data)
        assert "al menos 8 caracteres" in str(exc_info.value)

    @pytest.mark.parametrize("password", VALID_PASSWORDS)
    def test_accepts_password_of_eight_or_more(self, password):
        data = {"dni": "12345678901", "full_name": "Jane Doe", "password": password}
        patient = PatientCreate(**data)
        assert patient.password == password


class TestUserCreateEnforcesMinPassword:
    """UserCreate ya exigía 8; ahora usa la regla central sin debilitarse."""

    @pytest.mark.parametrize("password", SHORT_PASSWORDS)
    def test_rejects_short_password(self, password):
        data = {
            "dni": "12345678901",
            "password": password,
            "full_name": "John Doe",
        }
        with pytest.raises(ValidationError):
            UserCreate(**data)

    @pytest.mark.parametrize("password", VALID_PASSWORDS)
    def test_accepts_password_of_eight_or_more(self, password):
        data = {
            "dni": "12345678901",
            "password": password,
            "full_name": "John Doe",
        }
        user = UserCreate(**data)
        assert user.password == password


class TestStaffPasswordUpdateRequestEnforcesMinPassword:
    """StaffPasswordUpdateRequest exige 8 en new_password (F2-05, sin cambios de rigor)."""

    @pytest.mark.parametrize("password", SHORT_PASSWORDS)
    def test_rejects_short_new_password(self, password):
        with pytest.raises(ValidationError):
            StaffPasswordUpdateRequest(dni="12345678901", new_password=password)

    @pytest.mark.parametrize("password", VALID_PASSWORDS)
    def test_accepts_new_password_of_eight_or_more(self, password):
        req = StaffPasswordUpdateRequest(dni="12345678901", new_password=password)
        assert req.new_password == password


class TestAdminVerifyRequestEnforcesMinPassword:
    """AdminVerifyRequest exige 8 en password."""

    @pytest.mark.parametrize("password", SHORT_PASSWORDS)
    def test_rejects_short_password(self, password):
        with pytest.raises(ValidationError):
            AdminVerifyRequest(password=password)

    @pytest.mark.parametrize("password", VALID_PASSWORDS)
    def test_accepts_password_of_eight_or_more(self, password):
        req = AdminVerifyRequest(password=password)
        assert req.password == password
