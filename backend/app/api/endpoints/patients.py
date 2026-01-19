from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.triage_repository import TriageRepository
from app.repositories.user_repository import UserRepository
from app.schemas.patient import PatientExportData, TriageDataResponse, TriageDataUpdate

router = APIRouter(prefix="/patients", tags=["patients"])


@router.patch("/{patient_id}/medical-history", response_model=TriageDataResponse)
async def update_medical_history(
    patient_id: int,
    data: TriageDataUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TriageDataResponse:
    """
    Update or create patient medical history.
    
    This endpoint updates the medical_history field in the triage_data table.
    If no triage data exists for the patient, it creates a new record.
    
    SECURITY TODO: Add authentication middleware to verify:
    - The authenticated user's ID matches patient_id, OR
    - The authenticated user has appropriate role (doctor, admin, staff)
    This prevents unauthorized access to patient medical records.
    """
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
    
    return TriageDataResponse.model_validate(triage_data)


@router.get("/{patient_id}/medical-history", response_model=TriageDataResponse)
async def get_medical_history(
    patient_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TriageDataResponse:
    """
    Get patient medical history.
    
    Returns the patient's triage data including medical history and allergies.
    
    SECURITY TODO: Add authentication middleware to verify:
    - The authenticated user's ID matches patient_id, OR
    - The authenticated user has appropriate role (doctor, admin, staff)
    This prevents unauthorized access to patient medical records.
    """
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
) -> list[PatientExportData]:
    """
    List all patients with their medical data for export.
    
    Returns all patients with their basic information and triage data.
    This endpoint is intended for staff to export patient data to Excel.
    
    SECURITY TODO: Add authentication middleware to verify:
    - The authenticated user has role staff, admin, or doctor
    This prevents unauthorized access to all patient records.
    """
    # Get all patients
    user_repo = UserRepository(db)
    patients = await user_repo.get_all_patients()
    
    # Get all triage data
    triage_repo = TriageRepository(db)
    all_triage = await triage_repo.get_all()
    
    # Create a map of patient_id -> triage data for quick lookup
    triage_map = {triage.patient_id: triage for triage in all_triage}
    
    # Build response combining user and triage data
    result = []
    for patient in patients:
        triage = triage_map.get(patient.id)
        result.append(
            PatientExportData(
                id=patient.id,
                dni=patient.dni,
                full_name=patient.full_name,
                is_active=patient.is_active,
                medical_history=triage.medical_history if triage else None,
                allergies=triage.allergies if triage else None,
            )
        )
    
    return result
