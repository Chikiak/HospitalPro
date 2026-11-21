from datetime import datetime, timedelta, date as dt_date
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.appointment import Appointment, AppointmentStatus
from app.models.user import User, UserRole
from app.services.schedule_service import ScheduleService
from app.schemas.appointment import (
    AppointmentResponse,
    BookAppointmentRequest,
    TimeSlotResponse,
)

router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.get("/slots", response_model=List[TimeSlotResponse])
async def get_slots(
    category_name: str,
    category_type: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> List[TimeSlotResponse]:
    """
    Get the next 3 available time slots for a specific category.
    """
    schedule_service = ScheduleService(db)
    
    slots = await schedule_service.get_next_available_slots(category_name, category_type, limit=3)
    
    return [
        TimeSlotResponse(
            slot_datetime=slot.slot_datetime,
            category_name=slot.category_name,
            category_id=slot.category_id,
            warning_message=slot.warning_message,
            deadline_time=slot.deadline_time
        ) for slot in slots
    ]


@router.get("/me", response_model=List[AppointmentResponse])
async def get_my_appointments(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> List[AppointmentResponse]:
    """
    Get all appointments for the current authenticated patient.
    """
    query = select(Appointment).where(Appointment.patient_id == current_user.id).order_by(Appointment.appointment_date.desc())
    result = await db.execute(query)
    appointments = result.scalars().all()
    
    return [
        AppointmentResponse(
            id=app.id,
            patient_id=app.patient_id,
            patient_name=current_user.full_name,
            appointment_date=app.appointment_date,
            status=app.status,
            specialty=app.specialty,
            notes=app.notes
        ) for app in appointments
    ]


@router.post("/book", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def book_appointment(
    booking: BookAppointmentRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> AppointmentResponse:
    """
    Book an appointment slot using the authenticated user.
    """
    # Create the appointment using the provided data
    # doctor_id is no longer stored (category/specialty based)
    
    new_appointment = Appointment(
        patient_id=current_user.id,
        appointment_date=booking.appointment_date,
        specialty=booking.category_name,
        notes=booking.notes,
        status=AppointmentStatus.SCHEDULED,
    )
    
    db.add(new_appointment)
    await db.commit()
    await db.refresh(new_appointment)
    
    return AppointmentResponse(
        id=new_appointment.id,
        patient_id=new_appointment.patient_id,
        patient_name=current_user.full_name,
        appointment_date=new_appointment.appointment_date,
        status=new_appointment.status,
        specialty=new_appointment.specialty,
        notes=new_appointment.notes
    )


@router.put("/{appointment_id}/cancel", response_model=AppointmentResponse)
async def cancel_appointment(
    appointment_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> AppointmentResponse:
    """
    Cancel an appointment.
    Patients can only cancel their own appointments.
    Staff/Admins can cancel any appointment.
    """
    query = select(Appointment).where(Appointment.id == appointment_id).options(joinedload(Appointment.patient))
    result = await db.execute(query)
    appointment = result.scalar_one_or_none()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
        
    # Check permissions
    if current_user.role == UserRole.PATIENT and appointment.patient_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to cancel this appointment")
        
    appointment.status = AppointmentStatus.CANCELLED
    await db.commit()
    await db.refresh(appointment)
    
    return AppointmentResponse(
        id=appointment.id,
        patient_id=appointment.patient_id,
        patient_name=appointment.patient.full_name,
        appointment_date=appointment.appointment_date,
        status=appointment.status,
        specialty=appointment.specialty,
        notes=appointment.notes
    )


@router.get("/all", response_model=List[AppointmentResponse])
async def get_all_appointments(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    start_date: Optional[dt_date] = Query(None),
    end_date: Optional[dt_date] = Query(None),
    specialty: Optional[str] = Query(None),
) -> List[AppointmentResponse]:
    """
    Get all appointments with optional filters.
    Restricted to Staff/Admin/Doctor.
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.STAFF, UserRole.DOCTOR]:
        raise HTTPException(status_code=403, detail="Not authorized to view all appointments")
    
    query = select(Appointment).options(joinedload(Appointment.patient))
    conditions = []
    
    if start_date:
        # Convert date to datetime for proper comparison
        start_datetime = datetime.combine(start_date, datetime.min.time())
        conditions.append(Appointment.appointment_date >= start_datetime)
    
    if end_date:
        # Include the whole end date by going to midnight of the next day
        next_day = datetime.combine(end_date + timedelta(days=1), datetime.min.time())
        conditions.append(Appointment.appointment_date < next_day)
        
    if specialty:
        conditions.append(Appointment.specialty == specialty)
        
    if conditions:
        query = query.where(and_(*conditions))
        
    # Order by date descending
    query = query.order_by(Appointment.appointment_date.desc())
        
    result = await db.execute(query)
    appointments = result.scalars().all()
    
    return [
        AppointmentResponse(
            id=app.id,
            patient_id=app.patient_id,
            patient_name=app.patient.full_name,
            appointment_date=app.appointment_date,
            status=app.status,
            specialty=app.specialty,
            notes=app.notes
        ) for app in appointments
    ]


@router.get("/{appointment_id}/export")
async def export_patient_info(
    appointment_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Export patient medical history for a specific appointment to Excel.
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.STAFF, UserRole.DOCTOR]:
        raise HTTPException(status_code=403, detail="Not authorized")

    from app.models.patient import TriageData
    import pandas as pd
    import io
    from fastapi.responses import StreamingResponse

    # Get appointment and patient
    query = select(Appointment).where(Appointment.id == appointment_id).options(joinedload(Appointment.patient))
    result = await db.execute(query)
    appointment = result.scalar_one_or_none()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    # Get triage data
    triage_query = select(TriageData).where(TriageData.patient_id == appointment.patient_id)
    triage_result = await db.execute(triage_query)
    triage = triage_result.scalar_one_or_none()

    # Prepare data for Excel
    data = {
        "Campo": [
            "ID Paciente", 
            "DNI", 
            "Nombre Completo", 
            "Especialidad del Turno", 
            "Fecha del Turno",
            "Enfermedades Crónicas",
            "Alergias a Medicamentos",
            "Otra Información"
        ],
        "Información": [
            appointment.patient.id,
            appointment.patient.dni,
            appointment.patient.full_name,
            appointment.specialty,
            appointment.appointment_date.strftime("%Y-%m-%d %H:%M"),
            triage.medical_history.get("chronic_diseases", "") if triage and triage.medical_history else "No registrado",
            ", ".join(triage.medical_history.get("medication_allergies", [])) if triage and triage.medical_history and isinstance(triage.medical_history.get("medication_allergies"), list) else (triage.allergies or "No registrado"),
            triage.medical_history.get("other_information", "") if triage and triage.medical_history else "No registrado"
        ]
    }

    df = pd.DataFrame(data)
    
    # Create Excel in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Información del Paciente')
    
    output.seek(0)
    
    filename = f"paciente_{appointment.patient.dni}_{datetime.now().strftime('%Y%m%d')}.xlsx"
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
