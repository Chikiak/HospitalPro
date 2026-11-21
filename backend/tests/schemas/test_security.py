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
