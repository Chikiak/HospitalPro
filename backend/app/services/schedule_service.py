from datetime import datetime, timedelta, time as dt_time
from typing import List

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category_schedule import CategorySchedule, RotationType
from app.models.appointment import Appointment, AppointmentStatus


class TimeSlot:
    """Represents an available time slot."""
    
    def __init__(self, slot_datetime: datetime, category_name: str, category_id: int):
        self.slot_datetime = slot_datetime
        self.category_name = category_name
        self.category_id = category_id
    
    def __repr__(self):
        return f"TimeSlot(datetime={self.slot_datetime}, category={self.category_name})"


class ScheduleService:
    """Service for schedule operations with rotation logic."""
    
    # Anchor date for calculating alternating rotations (January 1, 2024)
    # This date is used as a reference point for week-based rotation calculations.
    # Weeks are calculated as complete 7-day periods since the anchor date.
    # Week 0 includes January 1-7, 2024; Week 1 is January 8-14, etc.
    ANCHOR_DATE = datetime(2024, 1, 1)
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_available_slots(
        self, 
        category_id: int, 
        date: datetime
    ) -> List[TimeSlot]:
        """
        Get available time slots for a category on a specific date.
        
        Args:
            category_id: The ID of the category schedule
            date: The date to check for available slots
        
        Returns:
            List of available TimeSlot objects
        
        Algorithm:
        1. Fetch the category schedule by ID
        2. Check if the schedule is active on the given date based on rotation logic:
           - FIXED: Available every week
           - ALTERNATED: Calculate week number from anchor date and check rotation
        3. Generate time slots based on start_time, turn_duration, and max_turns_per_block
        4. Filter out slots that are already occupied by appointments
        """
        # Fetch category schedule
        result = await self.session.execute(
            select(CategorySchedule).where(CategorySchedule.id == category_id)
        )
        category = result.scalar_one_or_none()
        
        if not category:
            return []
        
        # Check if the date matches the day of week
        if date.weekday() != category.day_of_week:
            return []
        
        # Check rotation logic
        if not self._is_schedule_active(category, date):
            return []
        
        # Generate all possible slots for this block
        slots = self._generate_slots(category, date)
        
        # Filter out occupied slots
        available_slots = await self._filter_occupied_slots(slots, category.name)
        
        return available_slots
    
    def _is_schedule_active(self, category: CategorySchedule, date: datetime) -> bool:
        """
        Determine if a schedule is active on a given date based on rotation type.
        
        Args:
            category: The category schedule
            date: The date to check
        
        Returns:
            True if the schedule is active on this date, False otherwise
        """
        if category.rotation_type == RotationType.FIXED:
            # FIXED schedules are available every week
            return True
        
        elif category.rotation_type == RotationType.ALTERNATED:
            # ALTERNATED schedules use week-based rotation
            # Calculate week number from anchor date
            days_since_anchor = (date.date() - self.ANCHOR_DATE.date()).days
            
            # For dates before anchor, treat as inactive (alternatively could raise an error)
            if days_since_anchor < 0:
                return False
            
            weeks_since_anchor = days_since_anchor // 7
            
            # Check if this week matches the rotation pattern
            # The schedule is active when: (current_week - anchor_week) % rotation_weeks == 0
            return (weeks_since_anchor % category.rotation_weeks) == 0
        
        return False
    
    def _generate_slots(self, category: CategorySchedule, date: datetime) -> List[TimeSlot]:
        """
        Generate all time slots for a category on a given date.
        
        Args:
            category: The category schedule
            date: The date for which to generate slots
        
        Returns:
            List of TimeSlot objects representing all possible slots
        """
        slots = []
        
        # Combine date with start time
        current_time = datetime.combine(date.date(), category.start_time)
        
        # Generate slots by adding turn_duration repeatedly
        for turn_number in range(category.max_turns_per_block):
            slot = TimeSlot(
                slot_datetime=current_time,
                category_name=category.name,
                category_id=category.id
            )
            slots.append(slot)
            
            # Add turn_duration (in minutes) to get the next slot
            current_time = current_time + timedelta(minutes=category.turn_duration)
        
        return slots
    
    async def _filter_occupied_slots(
        self, 
        slots: List[TimeSlot], 
        category_name: str
    ) -> List[TimeSlot]:
        """
        Filter out time slots that are already occupied by appointments.
        
        Args:
            slots: List of all potential time slots
            category_name: The name of the category (used to match with appointment.specialty)
        
        Returns:
            List of available (non-occupied) TimeSlot objects
        """
        if not slots:
            return []
        
        # Get all slot datetimes
        slot_datetimes = [slot.slot_datetime for slot in slots]
        
        # Query appointments that match these datetimes AND the category specialty
        # This ensures we only block slots for appointments of the same category
        result = await self.session.execute(
            select(Appointment).where(
                and_(
                    Appointment.appointment_date.in_(slot_datetimes),
                    Appointment.specialty == category_name,
                    Appointment.status.in_([
                        AppointmentStatus.SCHEDULED,
                        AppointmentStatus.CONFIRMED
                    ])
                )
            )
        )
        occupied_appointments = result.scalars().all()
        
        # Create a set of occupied datetimes for fast lookup
        occupied_datetimes = {appt.appointment_date for appt in occupied_appointments}
        
        # Filter out occupied slots
        available_slots = [
            slot for slot in slots 
            if slot.slot_datetime not in occupied_datetimes
        ]
        
        return available_slots
