from datetime import datetime, timedelta
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.appointment import Appointment, AppointmentStatus
from app.models.schedule import DoctorAvailability
from app.models.user import User, UserRole
from app.schemas.appointment import (
    AppointmentResponse,
    AvailableSlot,
    BookAppointmentRequest,
)

router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.get("/available", response_model=List[AvailableSlot])
async def get_available_appointments(
    specialty: str = Query(..., description="Medical specialty to filter by"),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> List[AvailableSlot]:
    """
    Get the next 3 available appointment slots for a given specialty.
    
    Algorithm:
    1. Find all doctors with the specified specialty and their availability schedules
    2. For each doctor, calculate the next available time slots based on:
       - Their weekly availability (DoctorAvailability)
       - Existing appointments (to avoid double-booking)
    3. Return the 3 closest available slots sorted by date
    """
    # Get current date and time
    now = datetime.now()
    
    # Find doctors with the specified specialty from their availability records
    availability_query = select(DoctorAvailability).where(
        DoctorAvailability.specialty == specialty
    )
    availability_result = await db.execute(availability_query)
    availabilities = availability_result.scalars().all()
    
    if not availabilities:
        return []
    
    # Get unique doctor IDs
    doctor_ids = list(set(avail.doctor_id for avail in availabilities))
    
    # Get doctor information
    doctors_query = select(User).where(
        and_(
            User.id.in_(doctor_ids),
            User.role == UserRole.DOCTOR,
            User.is_active == True
        )
    )
    doctors_result = await db.execute(doctors_query)
    doctors = {doctor.id: doctor for doctor in doctors_result.scalars().all()}
    
    # Generate potential slots for the next 30 days
    available_slots = []
    search_days = 30
    
    for doctor_id in doctor_ids:
        if doctor_id not in doctors:
            continue
            
        doctor = doctors[doctor_id]
        doctor_availabilities = [a for a in availabilities if a.doctor_id == doctor_id]
        
        # For each day in the search period
        for day_offset in range(search_days):
            check_date = now.date() + timedelta(days=day_offset)
            day_of_week = check_date.weekday()  # 0=Monday, 6=Sunday
            
            # Find availability for this day of week
            day_availabilities = [
                a for a in doctor_availabilities 
                if a.day_of_week.value == day_of_week
            ]
            
            for avail in day_availabilities:
                # Create datetime for this slot
                slot_datetime = datetime.combine(check_date, avail.start_time)
                
                # Skip past slots
                if slot_datetime <= now:
                    continue
                
                # Check if this slot is already booked
                existing_appointment_query = select(Appointment).where(
                    and_(
                        Appointment.doctor_id == doctor_id,
                        Appointment.appointment_date == slot_datetime,
                        Appointment.status.in_([
                            AppointmentStatus.SCHEDULED,
                            AppointmentStatus.CONFIRMED
                        ])
                    )
                )
                existing_result = await db.execute(existing_appointment_query)
                existing_appointment = existing_result.scalar_one_or_none()
                
                if not existing_appointment:
                    available_slots.append(
                        AvailableSlot(
                            doctor_id=doctor_id,
                            doctor_name=doctor.full_name,
                            specialty=specialty,
                            appointment_date=slot_datetime,
                        )
                    )
    
    # Sort by date and return the 3 closest slots
    available_slots.sort(key=lambda x: x.appointment_date)
    return available_slots[:3]


@router.post("/book", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def book_appointment(
    booking: BookAppointmentRequest,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> AppointmentResponse:
    """
    Book an appointment slot.
    
    This endpoint:
    1. Validates that the doctor exists and is active
    2. Checks that the slot is still available
    3. Creates the appointment
    
    SECURITY WARNING: This endpoint currently uses a hardcoded patient_id for testing.
    In production, this MUST be replaced with proper JWT authentication to get the
    actual patient_id from the authenticated user. Otherwise, any user could book
    appointments for any patient.
    
    Production requirements:
    - Implement JWT authentication dependency
    - Validate that the authenticated user is a patient
    - Use the authenticated user's ID as patient_id
    - Send confirmation notifications
    """
    # Verify doctor exists and is active
    doctor_query = select(User).where(
        and_(
            User.id == booking.doctor_id,
            User.role == UserRole.DOCTOR,
            User.is_active == True
        )
    )
    doctor_result = await db.execute(doctor_query)
    doctor = doctor_result.scalar_one_or_none()
    
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found or not active"
        )
    
    # Check if the slot is still available
    existing_appointment_query = select(Appointment).where(
        and_(
            Appointment.doctor_id == booking.doctor_id,
            Appointment.appointment_date == booking.appointment_date,
            Appointment.status.in_([
                AppointmentStatus.SCHEDULED,
                AppointmentStatus.CONFIRMED
            ])
        )
    )
    existing_result = await db.execute(existing_appointment_query)
    existing_appointment = existing_result.scalar_one_or_none()
    
    if existing_appointment:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This appointment slot is no longer available"
        )
    
    # SECURITY NOTE: This is a placeholder for patient_id
    # In production, this MUST be replaced with the authenticated user's ID
    # obtained from the JWT token via a proper dependency like:
    # current_user: User = Depends(get_current_user)
    # patient_id = current_user.id
    # 
    # TODO: Implement proper JWT authentication and replace this hardcoded value
    # This hardcoded value is only for testing purposes and creates a security vulnerability
    patient_id = 1  # SECURITY: Replace with authenticated user ID in production
    
    # Create the appointment
    new_appointment = Appointment(
        patient_id=patient_id,
        doctor_id=booking.doctor_id,
        appointment_date=booking.appointment_date,
        specialty=booking.specialty,
        notes=booking.notes,
        status=AppointmentStatus.SCHEDULED,
    )
    
    db.add(new_appointment)
    await db.commit()
    await db.refresh(new_appointment)
    
    return AppointmentResponse.model_validate(new_appointment)
