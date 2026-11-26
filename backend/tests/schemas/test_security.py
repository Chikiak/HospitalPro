"""Tests for security schemas."""
import pytest
from pydantic import ValidationError

from app.schemas.security import (
    AdminDniRequest,
    AdminVerifyRequest,
    StaffPasswordUpdateRequest,
)


class TestAdminVerifyRequest:
    """Test AdminVerifyRequest schema."""

    def test_admin_verify_request_valid_password(self):
        """AdminVerifyRequest accepts password of 8+ characters."""
        request = AdminVerifyRequest(password="securepass123")
        assert request.password == "securepass123"

    def test_admin_verify_request_rejects_short_password(self):
        """AdminVerifyRequest rejects passwords shorter than 8 characters."""
        with pytest.raises(ValidationError):
            AdminVerifyRequest(password="short1")

    def test_admin_verify_request_missing_password(self):
        """AdminVerifyRequest requires password field."""
        with pytest.raises(ValidationError):
            AdminVerifyRequest()


class TestStaffPasswordUpdateRequest:
    """Test StaffPasswordUpdateRequest schema."""

    def test_staff_password_update_request_valid(self):
        """StaffPasswordUpdateRequest accepts valid new_staff_password."""
        request = StaffPasswordUpdateRequest(
            new_staff_password="newstaffpass123",
        )
        assert request.new_staff_password == "newstaffpass123"

    def test_staff_password_update_request_rejects_short_new_password(self):
        """StaffPasswordUpdateRequest rejects new_staff_password shorter than 8."""
        with pytest.raises(ValidationError):
            StaffPasswordUpdateRequest(
                new_staff_password="short1",
            )

    def test_staff_password_update_request_ignores_extra_admin_password(self):
        """StaffPasswordUpdateRequest ignores admin_password if sent by legacy client (Pydantic extra='ignore')."""
        request = StaffPasswordUpdateRequest(
            new_staff_password="newstaffpass123",
            admin_password="should-be-ignored",
        )
        assert request.new_staff_password == "newstaffpass123"
        assert not hasattr(request, "admin_password")


class TestAdminDniRequest:
    """Test AdminDniRequest schema."""

    def test_admin_dni_request_valid_11_digits(self):
        """AdminDniRequest accepts a valid 11-digit DNI."""
        request = AdminDniRequest(
            dni="12345678901",
            full_name="Test User",
        )
        assert request.dni == "12345678901"

    def test_admin_dni_request_rejects_non_11_digit_dni(self):
        """AdminDniRequest rejects DNIs that are not exactly 11 digits."""
        with pytest.raises(ValidationError) as exc_info:
            AdminDniRequest(
                dni="12345",  # too short
            )
        assert "El DNI debe contener exactamente 11 dígitos numéricos" in str(exc_info.value)

    def test_admin_dni_request_rejects_non_numeric_dni(self):
        """AdminDniRequest rejects DNIs containing non-digit characters."""
        with pytest.raises(ValidationError) as exc_info:
            AdminDniRequest(
                dni="1234567890a",  # contains letter
            )
        assert "El DNI debe contener exactamente 11 dígitos numéricos" in str(exc_info.value)

    def test_admin_dni_request_without_full_name(self):
        """AdminDniRequest accepts DNI without optional full_name."""
        request = AdminDniRequest(
            dni="12345678901",
        )
        assert request.dni == "12345678901"
        assert request.full_name is None


def test_admin_dni_request_requires_11_digits():
    """AdminDniRequest acepta DNI de 11 dígitos numéricos y rechaza <11, >11 y no numéricos."""
    # 11 dígitos válidos
    request = AdminDniRequest(
        dni="12345678901",
    )
    assert request.dni == "12345678901"

    # Menos de 11 dígitos: mensaje en español
    with pytest.raises(ValidationError) as exc_info:
        AdminDniRequest(
            dni="1234567890",  # 10 dígitos
        )
    assert "El DNI debe contener exactamente 11 dígitos numéricos" in str(exc_info.value)

    # Más de 11 dígitos: mensaje en español
    with pytest.raises(ValidationError) as exc_info:
        AdminDniRequest(
            dni="123456789012",  # 12 dígitos
        )
    assert "El DNI debe contener exactamente 11 dígitos numéricos" in str(exc_info.value)

    # Caracteres no numéricos: mensaje en español
    with pytest.raises(ValidationError) as exc_info:
        AdminDniRequest(
            dni="1234567890a",  # contiene letra
        )
    assert "El DNI debe contener exactamente 11 dígitos numéricos" in str(exc_info.value)

    # Valor no string: mensaje en español
    with pytest.raises(ValidationError) as exc_info:
        AdminDniRequest(
            dni=12345678901,  # int en vez de str
        )
    assert "El DNI debe contener exactamente 11 dígitos numéricos" in str(exc_info.value)


def test_admin_password_min_length():
    """AdminVerifyRequest (password) y StaffPasswordUpdateRequest (new_staff_password) rechazan <8 y aceptan 8."""
    # AdminVerifyRequest acepta 8 caracteres
    req = AdminVerifyRequest(password="aaaaaaaa")
    assert req.password == "aaaaaaaa"

    # AdminVerifyRequest rechaza 7 caracteres (límite exacto)
    with pytest.raises(ValidationError):
        AdminVerifyRequest(password="aaaaaaa")

    # AdminVerifyRequest rechaza menos de 7
    with pytest.raises(ValidationError):
        AdminVerifyRequest(password="short1")

    # StaffPasswordUpdateRequest acepta 8 caracteres en new_staff_password
    req = StaffPasswordUpdateRequest(
        new_staff_password="newstaff",
    )
    assert req.new_staff_password == "newstaff"

    # StaffPasswordUpdateRequest rechaza new_staff_password de 7 caracteres
    with pytest.raises(ValidationError):
        StaffPasswordUpdateRequest(
            new_staff_password="newstaf",  # 7 caracteres
        )
