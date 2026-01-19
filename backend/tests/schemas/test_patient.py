"""Tests for patient schemas."""
import pytest
from pydantic import ValidationError

from app.schemas.patient import (
    PatientCreate,
    TriageUpdate,
    TriageDataCreate,
    TriageDataUpdate,
    TriageDataResponse
)


class TestPatientCreate:
    """Test PatientCreate schema."""
    
    def test_valid_patient_create(self):
        """Test creating a valid PatientCreate."""
        data = {
            "dni": "12345678901",
            "full_name": "Jane Doe",
            "password": "securepass123"
        }
        patient = PatientCreate(**data)
        assert patient.dni == "12345678901"
        assert patient.full_name == "Jane Doe"
        assert patient.password == "securepass123"
    
    def test_patient_create_with_invalid_dni_length(self):
        """Test PatientCreate with invalid DNI length."""
        data = {
            "dni": "123456789",  # Too short
            "full_name": "Jane Doe",
            "password": "securepass123"
        }
        with pytest.raises(ValidationError) as exc_info:
            PatientCreate(**data)
        assert "dni" in str(exc_info.value).lower()
    
    def test_patient_create_with_non_numeric_dni(self):
        """Test PatientCreate with non-numeric DNI."""
        data = {
            "dni": "1234567890a",  # Contains letter
            "full_name": "Jane Doe",
            "password": "securepass123"
        }
        with pytest.raises(ValidationError) as exc_info:
            PatientCreate(**data)
        assert "dni" in str(exc_info.value).lower()
    
    def test_patient_create_with_short_password(self):
        """Test PatientCreate with password too short."""
        data = {
            "dni": "12345678901",
            "full_name": "Jane Doe",
            "password": "short"
        }
        with pytest.raises(ValidationError) as exc_info:
            PatientCreate(**data)
        assert "at least 6 characters" in str(exc_info.value)
    
    def test_patient_create_missing_required_fields(self):
        """Test PatientCreate with missing required fields."""
        data = {"dni": "12345678901"}
        with pytest.raises(ValidationError) as exc_info:
            PatientCreate(**data)
        errors = str(exc_info.value).lower()
        assert "full_name" in errors or "password" in errors


class TestTriageUpdate:
    """Test TriageUpdate schema."""
    
    def test_valid_triage_update_full(self):
        """Test creating a valid TriageUpdate with all fields."""
        data = {
            "medical_history": {
                "chronic_conditions": ["diabetes", "hypertension"],
                "surgeries": ["appendectomy"],
                "medications": ["metformin"]
            },
            "allergies": "penicillin, peanuts"
        }
        triage = TriageUpdate(**data)
        assert triage.medical_history == data["medical_history"]
        assert triage.allergies == "penicillin, peanuts"
    
    def test_valid_triage_update_partial(self):
        """Test creating a TriageUpdate with only medical_history."""
        data = {
            "medical_history": {"chronic_conditions": ["diabetes"]}
        }
        triage = TriageUpdate(**data)
        assert triage.medical_history == data["medical_history"]
        assert triage.allergies is None
    
    def test_valid_triage_update_empty(self):
        """Test creating a TriageUpdate with no fields."""
        data = {}
        triage = TriageUpdate(**data)
        assert triage.medical_history is None
        assert triage.allergies is None
    
    def test_triage_update_with_allergies_only(self):
        """Test creating a TriageUpdate with only allergies."""
        data = {"allergies": "latex"}
        triage = TriageUpdate(**data)
        assert triage.medical_history is None
        assert triage.allergies == "latex"


class TestTriageDataCreate:
    """Test TriageDataCreate schema."""
    
    def test_valid_triage_data_create(self):
        """Test creating a valid TriageDataCreate."""
        data = {
            "patient_id": 1,
            "medical_history": {"conditions": ["asthma"]},
            "allergies": "dust"
        }
        triage_data = TriageDataCreate(**data)
        assert triage_data.patient_id == 1
        assert triage_data.medical_history == data["medical_history"]
        assert triage_data.allergies == "dust"


class TestTriageDataUpdate:
    """Test TriageDataUpdate schema."""
    
    def test_valid_triage_data_update(self):
        """Test creating a valid TriageDataUpdate."""
        data = {
            "medical_history": {"updated": True},
            "allergies": "none"
        }
        triage_data = TriageDataUpdate(**data)
        assert triage_data.medical_history == data["medical_history"]
        assert triage_data.allergies == "none"
