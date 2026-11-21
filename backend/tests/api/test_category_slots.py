import pytest
from datetime import time
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category_schedule import CategorySchedule, CategoryType, RotationType


@pytest.mark.asyncio
async def test_get_slots_without_date_param(client: AsyncClient, test_db: AsyncSession):
    """GET /appointments/slots sin `date`: hasta 3 slots en días distintos."""
    monday = CategorySchedule(
        category_type=CategoryType.SPECIALTY,
        name="Pediatria",
        day_of_week=0,  # Monday
        start_time=time(9, 0),
        turn_duration=30,
        max_turns_per_block=2,
        rotation_type=RotationType.FIXED,
    )
    wednesday = CategorySchedule(
        category_type=CategoryType.SPECIALTY,
        name="Pediatria",
        day_of_week=2,  # Wednesday
        start_time=time(14, 0),
        turn_duration=30,
        max_turns_per_block=2,
        rotation_type=RotationType.FIXED,
    )
    test_db.add(monday)
    test_db.add(wednesday)
    await test_db.commit()

    response = await client.get(
        "/appointments/slots",
        params={
            "category_name": "Pediatria",
            "category_type": "specialty",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 3

    # Cada slot debe caer en un día distinto
    days = {d["slot_datetime"][:10] for d in data}
    assert len(days) == len(data)
