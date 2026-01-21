import pytest
from datetime import datetime, time, date
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category_schedule import CategorySchedule, CategoryType, RotationType
from app.api.endpoints.auth import create_access_token

@pytest.mark.asyncio
async def test_get_slots_multi_day_search(client: AsyncClient, test_db: AsyncSession):
    """Test getting slots across multiple days (next 14 days)."""
    # 1. Create a schedule for Monday
    monday_cat = CategorySchedule(
        category_type=CategoryType.SPECIALTY,
        name="Pediatria",
        day_of_week=0,  # Monday
        start_time=time(9, 0),
        turn_duration=30,
        max_turns_per_block=2,
        rotation_type=RotationType.FIXED,
    )
    # 2. Create a schedule for Wednesday
    wednesday_cat = CategorySchedule(
        category_type=CategoryType.SPECIALTY,
        name="Pediatria",
        day_of_week=2,  # Wednesday
        start_time=time(14, 0),
        turn_duration=30,
        max_turns_per_block=2,
        rotation_type=RotationType.FIXED,
    )
    test_db.add(monday_cat)
    test_db.add(wednesday_cat)
    await test_db.commit()
    
    # 3. Query slots starting from a Sunday (2024-01-07)
    # Should find Monday (Jan 8) and Wednesday (Jan 10)
    test_date = "2024-01-07"
    response = await client.get(
        "/appointments/slots",
        params={
            "category_name": "Pediatria",
            "category_type": "specialty",
            "date": test_date
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Each day has 2 slots, and there are 2 Mondays and 2 Wednesdays in 14 days
    assert len(data) == 8
    # Check that we have slots from both days
    dates = [d["slot_datetime"] for d in data]
    assert any("2024-01-08T09:00:00" in d for d in dates)
    assert any("2024-01-10T14:00:00" in d for d in dates)
