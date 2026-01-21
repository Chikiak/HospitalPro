from datetime import datetime, timedelta, date as dt_date
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.appointment import Appointment, AppointmentStatus
from app.models.user import UserRole
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
            category_id=slot.category_id
        ) for slot in slots
    ]


from fastapi.security import OAuth2PasswordBearer
from app.core.security import decode_access_token
from app.models.user import User

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login/access-token")

async def get_current_user(
    token: Annotated[str, Depends(reusable_oauth2)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> User:
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    dni = payload.get("sub")
    if not dni:
        raise HTTPException(status_code=401, detail="Invalid token")
        
    from app.services.auth_service import AuthService
    auth_service = AuthService(db)
    user = await auth_service.get_user_by_dni(dni)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/me", response_model=List[AppointmentResponse])
async def get_my_appointments(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> List[AppointmentResponse]:
    """
    Get all appointments for the current authenticated patient.
    """
    from sqlalchemy import select
    
    query = select(Appointment).where(Appointment.patient_id == current_user.id).order_by(Appointment.appointment_date.desc())
    result = await db.execute(query)
    appointments = result.scalars().all()
    
    return [AppointmentResponse.model_validate(app) for app in appointments]


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
    
    return AppointmentResponse.model_validate(new_appointment)


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
    from sqlalchemy import select
    
    query = select(Appointment).where(Appointment.id == appointment_id)
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
    
    return AppointmentResponse.model_validate(appointment)


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
        
    from sqlalchemy import select, and_
    
    query = select(Appointment)
    conditions = []
    
    if start_date:
        conditions.append(Appointment.appointment_date >= start_date)
    
    if end_date:
        # Include the whole end date
        next_day = end_date + timedelta(days=1)
        conditions.append(Appointment.appointment_date < next_day)
        
    if specialty:
        conditions.append(Appointment.specialty == specialty)
        
    if conditions:
        query = query.where(and_(*conditions))
        
    # Order by date descending
    query = query.order_by(Appointment.appointment_date.desc())
        
    result = await db.execute(query)
    appointments = result.scalars().all()
    
    return [AppointmentResponse.model_validate(app) for app in appointments]
