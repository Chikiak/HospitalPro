from datetime import datetime, timedelta, time as dt_time
from typing import List, Union, Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category_schedule import CategorySchedule, RotationType, CategoryType
from app.models.appointment import Appointment, AppointmentStatus


class TimeSlot:
    """Represents an available time slot."""
    
    def __init__(self, slot_datetime: datetime, category_name: str, category_id: int, 
                 warning_message: str = None, deadline_time: str = None):
        self.slot_datetime = slot_datetime
        self.category_name = category_name
        self.category_id = category_id
        self.warning_message = warning_message
        self.deadline_time = deadline_time
    
    def __repr__(self):
        return f"TimeSlot(datetime={self.slot_datetime}, category={self.category_name})"


class ScheduleService:
    """Service for schedule operations with rotation logic."""
    
    # Anchor date for calculating alternating rotations (January 1, 2024)
    ANCHOR_DATE = datetime(2024, 1, 1)
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_next_available_slots(
        self, 
        category_name: str,
        category_type: str,
        limit: int = 3
    ) -> List[TimeSlot]:
        """
        Get the next available time slots for a category.
        Ensures 3 DIFFERENT days are returned in the top suggestions.
        """
        all_available_slots = []
        start_date = datetime.now()
        
        # Fetch all schedules for this category name and type
        result = await self.session.execute(
            select(CategorySchedule).where(
                and_(
                    CategorySchedule.name == category_name,
                    CategorySchedule.category_type == category_type
                )
            )
        )
        schedules = result.scalars().all()
        
        if not schedules:
            return []

        # Map day_of_week to schedules
        schedules_by_day = {s.day_of_week: s for s in schedules}
        valid_days = set(schedules_by_day.keys())
        
        days_searched = 0
        current_date_cursor = start_date

        while len(all_available_slots) < limit and days_searched < 60:
            if current_date_cursor.weekday() in valid_days:
                category = schedules_by_day[current_date_cursor.weekday()]
                
                if self._is_schedule_active(category, current_date_cursor):
                    slots = self._generate_slots(category, current_date_cursor)
                    
                    if current_date_cursor.date() == datetime.now().date():
                        now = datetime.now()
                        slots = [s for s in slots if s.slot_datetime > now]
                    
                    if slots:
                        # Validate availability based on strict rules
                        available_slots = await self._filter_occupied_slots(
                            slots, 
                            category.name, 
                            category.category_type,
                            category.max_turns_per_block
                        )
                        
                        # Requirement: Ensure distinct days in suggestions
                        if available_slots:
                            all_available_slots.append(available_slots[0])
            
            current_date_cursor += timedelta(days=1)
            days_searched += 1
            
            if len(all_available_slots) >= limit:
                break
        
        return all_available_slots
    
    def _is_schedule_active(self, category: CategorySchedule, date: datetime) -> bool:
        if category.rotation_type == RotationType.FIXED:
            return True
        elif category.rotation_type == RotationType.ALTERNATED:
            anchor_date = category.start_date if category.start_date else self.ANCHOR_DATE.date()
            if isinstance(anchor_date, datetime):
                anchor_date = anchor_date.date()
            days_since_anchor = (date.date() - anchor_date).days
            if days_since_anchor < 0:
                return False
            weeks_since_anchor = days_since_anchor // 7
            if category.rotation_weeks > 1:
                return (weeks_since_anchor % category.rotation_weeks) == 0
            return True
        return False
    
    def _generate_slots(self, category: CategorySchedule, date: datetime) -> List[TimeSlot]:
        slots = []
        slot_time = datetime.combine(date.date(), category.start_time)
        
        is_lab = category.category_type == CategoryType.LABORATORY
        if is_lab:
            arrival_time = (slot_time - timedelta(minutes=30)).strftime("%H:%M")
            warning_message = f"⚠️ IMPORTANTE: Debe presentarse a las {arrival_time}. No recibimos muestras después de la hora límite."
        else:
            warning_message = category.warning_message
            
        deadline_time = category.deadline_time.strftime("%H:%M") if category.deadline_time else None
        
        for turn_number in range(category.max_turns_per_block):
            if category.deadline_time:
                deadline_dt = datetime.combine(date.date(), category.deadline_time)
                if slot_time >= deadline_dt:
                    break

            slot = TimeSlot(
                slot_datetime=slot_time,
                category_name=category.name,
                category_id=category.id,
                warning_message=warning_message,
                deadline_time=deadline_time
            )
            slots.append(slot)
            
            if not is_lab:
                slot_time = slot_time + timedelta(minutes=category.turn_duration)
        
        return slots

    def is_bookable_slot(self, category: CategorySchedule, appointment_date: datetime) -> bool:
        """
        Indica si ``appointment_date`` es un slot reservable para la categoría.

        Reutiliza las mismas reglas que alimentan GET /appointments/slots:
        - día de la semana coincide con CategorySchedule.day_of_week
        - el calendario está activo según rotation_type / start_date / rotation_weeks
        - la hora cae en una franja exacta (start_time + k*turn_duration)
          respetando deadline_time
        """
        if appointment_date.weekday() != category.day_of_week:
            return False

        if not self._is_schedule_active(category, appointment_date):
            return False

        is_lab = category.category_type == CategoryType.LABORATORY
        slot_time = datetime.combine(appointment_date.date(), category.start_time)

        for _ in range(category.max_turns_per_block):
            if category.deadline_time:
                deadline_dt = datetime.combine(appointment_date.date(), category.deadline_time)
                if slot_time >= deadline_dt:
                    break
            if slot_time == appointment_date:
                return True
            if not is_lab:
                slot_time = slot_time + timedelta(minutes=category.turn_duration)

        return False
    
    async def _filter_occupied_slots(
        self, 
        slots: List[TimeSlot], 
        category_name: str,
        category_type: CategoryType,
        max_turns: int
    ) -> List[TimeSlot]:
        """
        Filter out time slots that are already occupied by appointments.
        Enforces:
        - Specialties: 1 turn per day limit.
        - Laboratories: Capacity tracking for the same time.
        """
        if not slots:
            return []
        
        start_date = min(s.slot_datetime for s in slots).replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
        
        result = await self.session.execute(
            select(Appointment).where(
                and_(
                    Appointment.appointment_date >= start_date,
                    Appointment.appointment_date < end_date,
                    Appointment.specialty == category_name,
                    Appointment.status.in_([
                        AppointmentStatus.SCHEDULED,
                        AppointmentStatus.CONFIRMED
                    ])
                )
            )
        )
        occupied_appointments = result.scalars().all()
        
        if category_type == CategoryType.SPECIALTY:
            # If any appointment exists for this specialty today, no slots available.
            if occupied_appointments:
                return []
            return slots
        
        elif category_type == CategoryType.LABORATORY:
            counts = {}
            for appt in occupied_appointments:
                counts[appt.appointment_date] = counts.get(appt.appointment_date, 0) + 1
            
            return [
                slot for slot in slots
                if counts.get(slot.slot_datetime, 0) < max_turns
            ]
        
        return slots
