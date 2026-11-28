import json
from datetime import date, datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# Size limits (write boundary).
_MAX_ENTRY_RESULTS_CHARS = 5000
_MAX_MEDICAL_HISTORY_CHARS = 10000


class MedicalRecordEntryCreate(BaseModel):
    """Schema for creating a new medical record entry.

    Strict write schema: only the known keys below are accepted, with constrained
    types and size limits. Unknown keys, invalid types or oversized values are
    rejected by Pydantic (FastAPI returns 422) before anything is written.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "entry_type": "consultation",
                "specialty": "Cardiology",
                "doctor_name": "Dr. Juan Pérez",
                "diagnosis": "Hypertension",
                "notes": "Patient advised to reduce salt intake",
            }
        },
    )

    entry_type: Literal["consultation", "lab_result"] = Field(
        ..., description="Type of entry: 'consultation' or 'lab_result'"
    )
    specialty: Optional[str] = Field(
        None, max_length=100, description="Medical specialty"
    )
    doctor_name: Optional[str] = Field(
        None, max_length=200, description="Name of the attending doctor"
    )
    diagnosis: Optional[str] = Field(
        None, max_length=1000, description="Diagnosis or findings"
    )
    notes: Optional[str] = Field(
        None, max_length=2000, description="Additional notes"
    )
    results: Optional[dict[str, Any]] = Field(
        None, description="Lab results or other structured data"
    )

    @field_validator("results")
    @classmethod
    def _validate_results_size(cls, v: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
        if v is None:
            return v
        if len(json.dumps(v, ensure_ascii=False)) > _MAX_ENTRY_RESULTS_CHARS:
            raise ValueError("results excede el tamaño máximo permitido")
        return v


class MedicalHistoryWrite(BaseModel):
    """Strict write schema for the ``medical_history`` JSON dict.

    Whitelists every key observed in the real admission/registration flows
    (RegisterStep2, AdmissionForm, ExportExcel, Profile, existing tests) and
    forbids any unknown key. String fields carry sensible length limits;
    list-of-string fields carry size limits. Unknown keys, invalid types or
    oversized values are rejected (422) before writing.

    Read paths (TriageDataResponse, MedicalRecordResponse) intentionally keep
    ``dict[str, Any]`` so legacy records already stored are readable without any
    migration. Only the write boundary is validated.
    """

    model_config = ConfigDict(extra="forbid")

    # Observed keys across the real flows (RegisterStep2, ExportExcel, Profile, tests).
    chronic_diseases: Optional[str | list[str]] = Field(
        None, description="Chronic diseases (text or list)"
    )
    medication_allergies: Optional[str | list[str]] = Field(
        None, description="Medication allergies (text or list)"
    )
    other_information: Optional[str] = Field(
        None, max_length=4000, description="Other medical information"
    )
    allergies: Optional[str | list[str]] = Field(
        None, description="Allergies (text or list)"
    )
    previous_surgeries: Optional[str] = Field(
        None, max_length=2000, description="Previous surgeries"
    )
    current_medications: Optional[str] = Field(
        None, max_length=2000, description="Current medications"
    )
    family_history: Optional[str] = Field(
        None, max_length=2000, description="Family medical history"
    )
    habits: Optional[str] = Field(
        None, max_length=2000, description="Patient habits"
    )
    other_medical_info: Optional[str] = Field(
        None, max_length=2000, description="Other medical info"
    )
    conditions: Optional[list[str]] = Field(
        None, description="List of conditions"
    )
    condition: Optional[str] = Field(
        None, max_length=2000, description="Condition (singular)"
    )
    chronic_conditions: Optional[list[str]] = Field(
        None, description="List of chronic conditions"
    )
    surgeries: Optional[list[str]] = Field(
        None, description="List of surgeries"
    )
    medications: Optional[list[str]] = Field(
        None, description="List of medications"
    )
    updated: Optional[bool] = Field(
        None, description="Update flag"
    )
    phone: Optional[str] = Field(
        None,
        pattern=r"^\d{7,15}$",
        max_length=15,
        description="Teléfono de contacto del paciente",
    )
    emergency_contact: Optional[str] = Field(
        None,
        pattern=r"^\d{7,15}$",
        max_length=15,
        description="Teléfono de contacto de emergencia",
    )
    date_of_birth: Optional[str] = Field(
        None, description="Fecha de nacimiento del paciente (ISO date, YYYY-MM-DD)"
    )
    vitals: Optional[dict[str, Any]] = Field(
        None,
        description="Signos vitales (temperatura, heart_rate, presión, saturación, peso)",
    )

    @field_validator("date_of_birth", mode="before")
    @classmethod
    def _validate_date_of_birth(cls, v: Any) -> Any:
        if v is None:
            return v
        if not isinstance(v, str):
            raise ValueError("date_of_birth debe ser una fecha ISO (YYYY-MM-DD)")
        try:
            date.fromisoformat(v)
        except ValueError:
            raise ValueError("date_of_birth debe ser una fecha ISO válida (YYYY-MM-DD)")
        return v

    @field_validator("vitals")
    @classmethod
    def _validate_vitals_size(cls, v: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
        if v is None:
            return v
        if len(json.dumps(v, ensure_ascii=False)) > _MAX_ENTRY_RESULTS_CHARS:
            raise ValueError("vitals excede el tamaño máximo permitido")
        return v

    @model_validator(mode="after")
    def _validate_total_size(self) -> "MedicalHistoryWrite":
        total = len(
            json.dumps(self.model_dump(exclude_none=True), ensure_ascii=False)
        )
        if total > _MAX_MEDICAL_HISTORY_CHARS:
            raise ValueError("medical_history excede el tamaño máximo permitido")
        return self


class MedicalRecordResponse(BaseModel):
    """Schema for medical record response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    registration_survey: Optional[dict[str, Any]] = None
    entries: list[dict[str, Any]] = []
    created_at: datetime
    last_updated: datetime


class AllowedPersonCreate(BaseModel):
    """Schema for creating an allowed person."""

    dni: str = Field(..., description="DNI of the person")
    full_name: Optional[str] = Field(None, description="Full name of the person")


class AllowedPersonBulkCreate(BaseModel):
    """Schema for bulk creating allowed persons."""

    persons: list[AllowedPersonCreate] = Field(..., description="List of persons to add")
