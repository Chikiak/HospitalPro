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
        """StaffPasswordUpdateRequest accepts valid passwords."""
        request = StaffPasswordUpdateRequest(
            admin_password="adminpass123",
            new_staff_password="newstaffpass123",
        )
        assert request.admin_password == "adminpass123"
        assert request.new_staff_password == "newstaffpass123"

    def test_staff_password_update_request_rejects_short_admin_password(self):
        """StaffPasswordUpdateRequest rejects admin_password shorter than 8."""
        with pytest.raises(ValidationError):
            StaffPasswordUpdateRequest(
                admin_password="short1",
                new_staff_password="newstaffpass123",
            )

    def test_staff_password_update_request_rejects_short_new_password(self):
        """StaffPasswordUpdateRequest rejects new_staff_password shorter than 8."""
        with pytest.raises(ValidationError):
            StaffPasswordUpdateRequest(
                admin_password="adminpass123",
                new_staff_password="short1",
            )


class TestAdminDniRequest:
    """Test AdminDniRequest schema."""

    def test_admin_dni_request_valid_11_digits(self):
        """AdminDniRequest accepts a valid 11-digit DNI."""
        request = AdminDniRequest(
            admin_password="adminpass123",
            dni="12345678901",
            full_name="Test User",
        )
        assert request.dni == "12345678901"

    def test_admin_dni_request_rejects_non_11_digit_dni(self):
        """AdminDniRequest rejects DNIs that are not exactly 11 digits."""
        with pytest.raises(ValidationError):
            AdminDniRequest(
                admin_password="adminpass123",
                dni="12345",  # too short
            )

    def test_admin_dni_request_rejects_non_numeric_dni(self):
        """AdminDniRequest rejects DNIs containing non-digit characters."""
        with pytest.raises(ValidationError):
            AdminDniRequest(
                admin_password="adminpass123",
                dni="1234567890a",  # contains letter
            )

    def test_admin_dni_request_without_full_name(self):
        """AdminDniRequest accepts DNI without optional full_name."""
        request = AdminDniRequest(
            admin_password="adminpass123",
            dni="12345678901",
        )
        assert request.dni == "12345678901"
        assert request.full_name is None


def test_admin_dni_request_requires_11_digits():
    """AdminDniRequest acepta DNI de 11 dígitos numéricos y rechaza <11, >11 y no numéricos."""
    # 11 dígitos válidos
    request = AdminDniRequest(
        admin_password="adminpass123",
        dni="12345678901",
    )
    assert request.dni == "12345678901"

    # Menos de 11 dígitos: mensaje en español
    with pytest.raises(ValidationError) as exc_info:
        AdminDniRequest(
            admin_password="adminpass123",
            dni="1234567890",  # 10 dígitos
        )
    assert "11 dígitos numéricos" in str(exc_info.value)

    # Más de 11 dígitos: mensaje en español
    with pytest.raises(ValidationError) as exc_info:
        AdminDniRequest(
            admin_password="adminpass123",
            dni="123456789012",  # 12 dígitos
        )
    assert "11 dígitos numéricos" in str(exc_info.value)

    # Caracteres no numéricos: mensaje en español
    with pytest.raises(ValidationError) as exc_info:
        AdminDniRequest(
            admin_password="adminpass123",
            dni="1234567890a",  # contiene letra
        )
    assert "11 dígitos numéricos" in str(exc_info.value)

    # Valor no string: mensaje en español
    with pytest.raises(ValidationError) as exc_info:
        AdminDniRequest(
            admin_password="adminpass123",
            dni=12345678901,  # int en vez de str
        )
    assert "11 dígitos numéricos" in str(exc_info.value)


def test_admin_password_min_length():
    """AdminVerifyRequest (password) y StaffPasswordUpdateRequest (admin_password y new_staff_password) rechazan <8 y aceptan 8."""
    # AdminVerifyRequest acepta 8 caracteres
    req = AdminVerifyRequest(password="aaaaaaaa")
    assert req.password == "aaaaaaaa"

    # AdminVerifyRequest rechaza 7 caracteres (límite exacto)
    with pytest.raises(ValidationError):
        AdminVerifyRequest(password="aaaaaaa")

    # AdminVerifyRequest rechaza menos de 7
    with pytest.raises(ValidationError):
        AdminVerifyRequest(password="short1")

    # StaffPasswordUpdateRequest acepta 8 caracteres en ambos campos
    req = StaffPasswordUpdateRequest(
        admin_password="adminpass",
        new_staff_password="newstaff",
    )
    assert req.admin_password == "adminpass"
    assert req.new_staff_password == "newstaff"

    # StaffPasswordUpdateRequest rechaza admin_password de 7 caracteres
    with pytest.raises(ValidationError):
        StaffPasswordUpdateRequest(
            admin_password="adminp",  # 7 caracteres
            new_staff_password="newstaff",
        )

    # StaffPasswordUpdateRequest rechaza new_staff_password de 7 caracteres
    with pytest.raises(ValidationError):
        StaffPasswordUpdateRequest(
            admin_password="adminpass",
            new_staff_password="newstaf",  # 7 caracteres
        )
