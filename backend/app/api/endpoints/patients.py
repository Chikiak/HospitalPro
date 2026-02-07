from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.patient import TriageData
from app.models.user import User, UserRole
from app.repositories.triage_repository import TriageRepository
from app.repositories.user_repository import UserRepository
from app.repositories.medical_record_repository import MedicalRecordRepository
from app.repositories.allowed_person_repository import AllowedPersonRepository
from app.schemas.patient import PatientExportData, TriageDataResponse, TriageDataUpdate
from app.schemas.medical_record import (
    MedicalRecordResponse,
    MedicalRecordEntryCreate,
    AllowedPersonBulkCreate,
)

router = APIRouter(prefix="/patients", tags=["patients"])

# Initialize limiter
limiter = Limiter(key_func=get_remote_address)


@router.patch("/{patient_id}/medical-history", response_model=TriageDataResponse)
async def update_medical_history(
    patient_id: int,
    data: TriageDataUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> TriageDataResponse:
    """
    Update or create patient medical history.
    
    This endpoint updates the medical_history field in the triage_data table.
    If no triage data exists for the patient, it creates a new record.
    
    Requires authentication. Patients can only update their own medical history.
    Medical professionals (doctor, admin, staff) can update any patient's history.
    """
    # Check authorization: patients can only access their own data
    if current_user.role == UserRole.PATIENT and current_user.id != patient_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para acceder a los datos de otro paciente",
        )
    # Verify patient exists
    user_repo = UserRepository(db)
    patient = await user_repo.get_by_id(patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paciente no encontrado",
        )
    
    # Get or create triage data
    triage_repo = TriageRepository(db)
    triage_data = await triage_repo.get_by_patient_id(patient_id)
    
    if triage_data:
        # Update existing triage data
        triage_data = await triage_repo.update(
            triage_data=triage_data,
            medical_history=data.medical_history,
            allergies=data.allergies,
        )
    else:
        # Create new triage data
        triage_data = await triage_repo.create(
            patient_id=patient_id,
            medical_history=data.medical_history,
            allergies=data.allergies,
        )
    
    # Auto-create medical record if it doesn't exist
    medical_record_repo = MedicalRecordRepository(db)
    medical_record = await medical_record_repo.get_by_patient_id(patient_id)
    if not medical_record and data.medical_history:
        await medical_record_repo.create(
            patient_id=patient_id,
            registration_survey=data.medical_history
        )
    
    return TriageDataResponse.model_validate(triage_data)


@router.get("/{patient_id}/medical-history", response_model=TriageDataResponse)
async def get_medical_history(
    patient_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> TriageDataResponse:
    """
    Get patient medical history.
    
    Returns the patient's triage data including medical history and allergies.
    
    Requires authentication. Patients can only view their own medical history.
    Medical professionals (doctor, admin, staff) can view any patient's history.
    """
    # Check authorization: patients can only access their own data
    if current_user.role == UserRole.PATIENT and current_user.id != patient_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para acceder a los datos de otro paciente",
        )
    # Verify patient exists
    user_repo = UserRepository(db)
    patient = await user_repo.get_by_id(patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paciente no encontrado",
        )
    
    # Get triage data
    triage_repo = TriageRepository(db)
    triage_data = await triage_repo.get_by_patient_id(patient_id)
    
    if not triage_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró historial médico para este paciente",
        )
    
    return TriageDataResponse.model_validate(triage_data)


@router.get("/", response_model=list[PatientExportData])
async def list_all_patients(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role(["doctor", "admin", "staff"]))],
) -> list[PatientExportData]:
    """
    List all patients with their medical data for export.
    
    Returns all patients with their basic information and triage data.
    This endpoint is intended for staff to export patient data to Excel.
    Uses a single database query with a left join for optimal performance.
    
    Requires authentication and role: doctor, admin, or staff.
    Patients are not allowed to access this endpoint.
    """
    # Use a single query with left join to get patients and their triage data
    query = (
        select(User, TriageData)
        .outerjoin(TriageData, User.id == TriageData.patient_id)
        .where(User.role == UserRole.PATIENT)
        .order_by(User.id)
    )
    
    result = await db.execute(query)
    rows = result.all()
    
    # Build response from the joined results
    return [
        PatientExportData(
            id=user.id,
            dni=user.dni,
            full_name=user.full_name,
            is_active=user.is_active,
            medical_history=triage.medical_history if triage else None,
            allergies=triage.allergies if triage else None,
        )
        for user, triage in rows
    ]


@router.get("/{patient_id}/medical-record", response_model=MedicalRecordResponse)
async def get_medical_record(
    patient_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> MedicalRecordResponse:
    """
    Get patient's complete medical record.
    
    Returns the medical record including registration survey and all entries.
    
    Requires authentication. Patients can only view their own medical record.
    Medical professionals (doctor, admin, staff) can view any patient's record.
    """
    # Check authorization: patients can only access their own data
    if current_user.role == UserRole.PATIENT and current_user.id != patient_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para acceder a los datos de otro paciente",
        )
    # Verify patient exists
    user_repo = UserRepository(db)
    patient = await user_repo.get_by_id(patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paciente no encontrado",
        )
    
    # Get medical record
    medical_record_repo = MedicalRecordRepository(db)
    medical_record = await medical_record_repo.get_by_patient_id(patient_id)
    
    if not medical_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró historia clínica para este paciente",
        )
    
    return MedicalRecordResponse.model_validate(medical_record)


@router.post("/{patient_id}/medical-record/entries", response_model=MedicalRecordResponse)
async def add_medical_record_entry(
    patient_id: int,
    entry: MedicalRecordEntryCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role(["doctor", "admin", "staff"]))],
) -> MedicalRecordResponse:
    """
    Add a new entry to patient's medical record.
    
    Entries can be consultations or laboratory results.
    
    Requires authentication and role: doctor, admin, or staff.
    Only medical professionals can add entries to medical records.
    """
    # Verify patient exists
    user_repo = UserRepository(db)
    patient = await user_repo.get_by_id(patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paciente no encontrado",
        )
    
    # Add entry to medical record
    medical_record_repo = MedicalRecordRepository(db)
    try:
        medical_record = await medical_record_repo.add_entry(
            patient_id=patient_id,
            entry=entry.model_dump()
        )
        return MedicalRecordResponse.model_validate(medical_record)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/{patient_id}/medical-record/pdf")
@limiter.limit("10/minute")
async def get_medical_record_pdf(
    request: Request,
    patient_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Generate and download medical record as PDF.
    
    Rate limited to 10 requests per minute per IP to prevent resource exhaustion
    from PDF generation operations.
    
    Requires authentication. Patients can only download their own medical record.
    Medical professionals (doctor, admin, staff) can download any patient's record.
    """
    # Check authorization: patients can only access their own data
    if current_user.role == UserRole.PATIENT and current_user.id != patient_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para acceder a los datos de otro paciente",
        )
    from app.services.pdf_service import generate_medical_record_pdf
    
    # Verify patient exists
    user_repo = UserRepository(db)
    patient = await user_repo.get_by_id(patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paciente no encontrado",
        )
    
    # Generate PDF
    pdf_bytes = await generate_medical_record_pdf(patient_id, db)
    
    # Return as downloadable file
    return StreamingResponse(
        pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=historia_clinica_{patient_id}.pdf"
        }
    )


@router.post("/allowed-persons/bulk", status_code=status.HTTP_201_CREATED)
async def bulk_create_allowed_persons(
    data: AllowedPersonBulkCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role(["admin", "staff"]))],
):
    """
    Bulk create allowed persons (admin/staff only).
    
    Requires authentication and role: admin or staff.
    Only administrators can manage the allowed persons whitelist.
    """
    allowed_person_repo = AllowedPersonRepository(db)
    
    persons_data = [{"dni": p.dni, "full_name": p.full_name} for p in data.persons]
    created = await allowed_person_repo.bulk_create(persons_data)
    
    return {
        "message": f"Successfully created {len(created)} allowed persons",
        "count": len(created)
    }
