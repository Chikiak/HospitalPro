from datetime import datetime, timedelta, time as dt_time
from typing import List, Union, Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category_schedule import CategorySchedule, RotationType
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
    # This date is used as a reference point for week-based rotation calculations.
    # Weeks are calculated as complete 7-day periods since the anchor date.
    # Week 0 includes January 1-7, 2024; Week 1 is January 8-14, etc.
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
        
        Args:
            category_name: The name of the category
            category_type: The type of the category
            limit: Maximum number of slots to return (default 3)
            
        Returns:
            List of the next available TimeSlot objects
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

        # Optimize: Map day_of_week to schedules for faster lookup
        schedules_by_day = {s.day_of_week: s for s in schedules}
        valid_days = set(schedules_by_day.keys())
        
        # We'll search up to 60 days ahead to find slots (prevent infinite loop)
        days_searched = 0
        current_date_cursor = start_date

        while len(all_available_slots) < limit and days_searched < 60:
            # Check if current weekday is in our valid schedule days
            if current_date_cursor.weekday() in valid_days:
                category = schedules_by_day[current_date_cursor.weekday()]
                
                if self._is_schedule_active(category, current_date_cursor):
                    slots = self._generate_slots(category, current_date_cursor)
                    
                    # Filter out past slots if looking at today
                    if current_date_cursor.date() == datetime.now().date():
                        now = datetime.now()
                        slots = [s for s in slots if s.slot_datetime > now]
                    
                    if slots:
                        available_slots = await self._filter_occupied_slots(slots, category.name)
                        # BUG FIX: Only take the first available slot for this day
                        if available_slots:
                            all_available_slots.append(available_slots[0])
            
            # Move to next day
            current_date_cursor += timedelta(days=1)
            days_searched += 1
            
            # If we collected more than we need, trim list (though we append one by one now)
            if len(all_available_slots) >= limit:
                break
        
        return all_available_slots
    
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
            # Use category-specific start date if available, otherwise fallback to global anchor
            anchor_date = category.start_date if category.start_date else self.ANCHOR_DATE.date()
            
            # Ensure we are comparing dates
            if isinstance(anchor_date, datetime):
                anchor_date = anchor_date.date()
                
            # Calculate week number from anchor date
            days_since_anchor = (date.date() - anchor_date).days
            
            # For dates before anchor, treat as inactive
            if days_since_anchor < 0:
                return False
            
            weeks_since_anchor = days_since_anchor // 7
            
            # Check if this week matches the rotation pattern
            # The schedule is active when: (current_week - anchor_week) % rotation_weeks == 0
            if category.rotation_weeks > 1:
                return (weeks_since_anchor % category.rotation_weeks) == 0
            return True # Should not happen for alternating schedules with weeks=1, but fallback to True
        
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
        
        # Get warning message and deadline time from category
        warning_message = category.warning_message
        deadline_time = category.deadline_time.strftime("%H:%M") if category.deadline_time else None
        
        # Generate slots by adding turn_duration repeatedly
        for turn_number in range(category.max_turns_per_block):
            slot = TimeSlot(
                slot_datetime=current_time,
                category_name=category.name,
                category_id=category.id,
                warning_message=warning_message,
                deadline_time=deadline_time
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
