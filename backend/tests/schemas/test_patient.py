"""Tests for patient schemas."""
import pytest
from pydantic import ValidationError

from app.schemas.medical_record import MedicalHistoryWrite
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
    
    @pytest.mark.parametrize("password", ["short", "aaaaaaa", "1234567"])
    def test_patient_create_rejects_short_password(self, password):
        """Test PatientCreate rejects passwords shorter than 8 characters (F2-08)."""
        data = {
            "dni": "12345678901",
            "full_name": "Jane Doe",
            "password": password,
        }
        with pytest.raises(ValidationError) as exc_info:
            PatientCreate(**data)
        assert "al menos 8 caracteres" in str(exc_info.value)

    @pytest.mark.parametrize("password", ["aaaaaaaa", "securepass123"])
    def test_patient_create_accepts_password_of_eight_or_more(self, password):
        """Test PatientCreate accepts passwords of 8 or more characters (F2-08)."""
        data = {
            "dni": "12345678901",
            "full_name": "Jane Doe",
            "password": password,
        }
        patient = PatientCreate(**data)
        assert patient.password == password
    
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
        assert triage.medical_history.model_dump(exclude_none=True) == data["medical_history"]
        assert triage.allergies == "penicillin, peanuts"
    
    def test_valid_triage_update_partial(self):
        """Test creating a TriageUpdate with only medical_history."""
        data = {
            "medical_history": {"chronic_conditions": ["diabetes"]}
        }
        triage = TriageUpdate(**data)
        assert triage.medical_history.model_dump(exclude_none=True) == data["medical_history"]
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
        assert triage_data.medical_history.model_dump(exclude_none=True) == data["medical_history"]
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
        assert triage_data.medical_history.model_dump(exclude_none=True) == data["medical_history"]
        assert triage_data.allergies == "none"


class TestMedicalHistoryWrite:
    """Test MedicalHistoryWrite schema (admission whitelist extension, PR 1)."""

    def test_accepts_admission_fields(self):
        """MedicalHistoryWrite acepta phone, emergency_contact, date_of_birth y vitals."""
        data = {
            "phone": "3001234567",
            "emergency_contact": "3009876543",
            "date_of_birth": "1985-04-12",
            "vitals": {"temperatura": "36.5", "heart_rate": "72"},
        }
        mh = MedicalHistoryWrite(**data)
        dump = mh.model_dump(exclude_none=True)
        assert dump["phone"] == "3001234567"
        assert dump["emergency_contact"] == "3009876543"
        assert dump["date_of_birth"] == "1985-04-12"
        assert dump["vitals"] == {"temperatura": "36.5", "heart_rate": "72"}

    def test_rejects_unknown_key(self):
        """Una clave desconocida sigue siendo rechazada (extra=forbid)."""
        with pytest.raises(ValidationError) as exc_info:
            MedicalHistoryWrite(campo_inexistente="x")
        assert "extra_forbidden" in str(exc_info.value) or "Extra inputs are not permitted" in str(exc_info.value)

    def test_rejects_invalid_date_of_birth(self):
        """date_of_birth debe ser una fecha ISO válida."""
        with pytest.raises(ValidationError):
            MedicalHistoryWrite(date_of_birth="not-a-date")

    def test_rejects_phone_wrong_pattern(self):
        """phone debe cumplir el patrón de solo dígitos (7-15)."""
        with pytest.raises(ValidationError):
            MedicalHistoryWrite(phone="abc")
        with pytest.raises(ValidationError):
            MedicalHistoryWrite(phone="12")  # muy corto

    @pytest.mark.parametrize("phone", ["3001234567", "1234567", "30012345678901"])
    def test_accepts_valid_phone(self, phone):
        """Teléfonos de 7 a 15 dígitos son válidos."""
        mh = MedicalHistoryWrite(phone=phone)
        assert mh.phone == phone

    def test_allows_none_for_all_fields(self):
        """Todos los campos son opcionales."""
        mh = MedicalHistoryWrite()
        assert mh.model_dump(exclude_none=True) == {}
