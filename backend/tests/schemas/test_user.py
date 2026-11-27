"""Tests for user schemas."""
import pytest
from pydantic import ValidationError

from app.schemas.auth import StaffLoginRequest
from app.schemas.user import UserCreate, UserResponse
from app.models.user import UserRole


class TestStaffLoginRequest:
    """Test StaffLoginRequest schema (F2-05: dni + password vs real STAFF user)."""

    def test_valid_staff_login_request(self):
        """Test creating a valid StaffLoginRequest with DNI and password."""
        data = {"dni": "12345678901", "password": "securepass123"}
        request = StaffLoginRequest(**data)
        assert request.dni == "12345678901"
        assert request.password == "securepass123"

    def test_staff_login_request_requires_dni(self):
        """StaffLoginRequest requires a DNI."""
        data = {"password": "securepass123"}
        with pytest.raises(ValidationError) as exc_info:
            StaffLoginRequest(**data)
        assert "dni" in str(exc_info.value).lower()

    def test_staff_login_request_rejects_bad_dni(self):
        """StaffLoginRequest rejects DNIs that are not exactly 11 digits."""
        for dni in ("12345", "123456789012", "1234567890a"):
            data = {"dni": dni, "password": "securepass123"}
            with pytest.raises(ValidationError):
                StaffLoginRequest(**data)

    def test_staff_login_request_requires_password(self):
        """StaffLoginRequest requires a password."""
        data = {"dni": "12345678901"}
        with pytest.raises(ValidationError) as exc_info:
            StaffLoginRequest(**data)
        assert "password" in str(exc_info.value).lower()


class TestUserCreate:
    """Test UserCreate schema."""
    
    def test_valid_user_create(self):
        """Test creating a valid UserCreate."""
        data = {
            "dni": "12345678901",
            "password": "securepass123",
            "full_name": "John Doe",
            "role": UserRole.PATIENT
        }
        user = UserCreate(**data)
        assert user.dni == "12345678901"
        assert user.password == "securepass123"
        assert user.full_name == "John Doe"
        assert user.role == UserRole.PATIENT
    
    def test_user_create_default_role(self):
        """Test UserCreate with default role."""
        data = {
            "dni": "12345678901",
            "password": "securepass123",
            "full_name": "John Doe"
        }
        user = UserCreate(**data)
        assert user.role == UserRole.PATIENT

    def test_user_create_rejects_short_password(self):
        """UserCreate rejects passwords shorter than 8 characters (incluye el límite de 7)."""
        for password in ("short1", "aaaaaaa", "1234567"):
            data = {
                "dni": "12345678901",
                "password": password,
                "full_name": "John Doe",
            }
            with pytest.raises(ValidationError):
                UserCreate(**data)

    def test_user_create_rejects_bad_dni(self):
        """UserCreate rejects DNIs que no sean exactamente 11 dígitos numéricos."""
        # Menos de 11 dígitos
        data = {
            "dni": "12345",
            "password": "securepass123",
            "full_name": "John Doe",
        }
        with pytest.raises(ValidationError):
            UserCreate(**data)

        # Más de 11 dígitos
        data["dni"] = "123456789012"
        with pytest.raises(ValidationError):
            UserCreate(**data)

        # Caracteres no numéricos
        data["dni"] = "1234567890a"
        with pytest.raises(ValidationError):
            UserCreate(**data)


class TestUserResponse:
    """Test UserResponse schema."""
    
    def test_valid_user_response(self):
        """Test creating a valid UserResponse."""
        data = {
            "id": 1,
            "dni": "12345678901",
            "full_name": "John Doe",
            "role": UserRole.PATIENT,
            "is_active": True
        }
        response = UserResponse(**data)
        assert response.id == 1
        assert response.dni == "12345678901"
        assert response.full_name == "John Doe"
        assert response.role == UserRole.PATIENT
        assert response.is_active is True
