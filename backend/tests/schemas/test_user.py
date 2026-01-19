"""Tests for user schemas."""
import pytest
from pydantic import ValidationError

from app.schemas.user import StaffLoginRequest, UserCreate, UserResponse
from app.models.user import UserRole


class TestStaffLoginRequest:
    """Test StaffLoginRequest schema."""
    
    def test_valid_staff_login_request(self):
        """Test creating a valid StaffLoginRequest."""
        data = {"password": "securepass123"}
        request = StaffLoginRequest(**data)
        assert request.password == "securepass123"
    
    def test_staff_login_request_with_short_password(self):
        """Test StaffLoginRequest with password too short."""
        data = {"password": "short"}
        with pytest.raises(ValidationError) as exc_info:
            StaffLoginRequest(**data)
        assert "at least 6 characters" in str(exc_info.value)
    
    def test_staff_login_request_missing_password(self):
        """Test StaffLoginRequest without password field."""
        data = {}
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
