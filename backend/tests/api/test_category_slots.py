import pytest
from datetime import datetime, time
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category_schedule import CategorySchedule, CategoryType, RotationType


@pytest.mark.asyncio
async def test_public_categories_without_auth(client: AsyncClient, test_db: AsyncSession):
    """GET /appointments/categories es público: 200 sin token."""
    test_db.add(
        CategorySchedule(
            category_type=CategoryType.SPECIALTY,
            name="Cardiology",
            day_of_week=0,
            start_time=time(9, 0),
            turn_duration=30,
            max_turns_per_block=4,
            rotation_type=RotationType.FIXED,
        )
    )
    test_db.add(
        CategorySchedule(
            category_type=CategoryType.LABORATORY,
            name="Blood Test",
            day_of_week=2,
            start_time=time(8, 0),
            turn_duration=15,
            max_turns_per_block=8,
            rotation_type=RotationType.FIXED,
        )
    )
    await test_db.commit()

    response = await client.get("/appointments/categories")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2


@pytest.mark.asyncio
async def test_public_categories_minimal_fields(client: AsyncClient, test_db: AsyncSession):
    """El catálogo público solo expone id, name y category_type (no plantilla admin)."""
    test_db.add(
        CategorySchedule(
            category_type=CategoryType.SPECIALTY,
            name="Cardiology",
            day_of_week=0,
            start_time=time(9, 0),
            turn_duration=30,
            max_turns_per_block=4,
            rotation_type=RotationType.FIXED,
        )
    )
    await test_db.commit()

    response = await client.get("/appointments/categories")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    item = data[0]
    assert set(item.keys()) == {"id", "name", "category_type"}
    assert item["name"] == "Cardiology"
    assert item["category_type"] == "specialty"
    # No debe exponer la plantilla administrativa
    for field in ("start_time", "turn_duration", "day_of_week", "rotation_type"):
        assert field not in item, f"el catálogo público no debe exponer {field}"


@pytest.mark.asyncio
async def test_public_categories_dedupe_by_name(client: AsyncClient, test_db: AsyncSession):
    """Una categoría con varios horarios (días) aparece una sola vez."""
    for day in (0, 2):
        test_db.add(
            CategorySchedule(
                category_type=CategoryType.SPECIALTY,
                name="Cardiology",
                day_of_week=day,
                start_time=time(9, 0),
                turn_duration=30,
                max_turns_per_block=4,
                rotation_type=RotationType.FIXED,
            )
        )
    await test_db.commit()

    response = await client.get("/appointments/categories")
    assert response.status_code == 200
    data = response.json()
    names = [item["name"] for item in data]
    assert names.count("Cardiology") == 1


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
    # Hay 2 horarios FIXED configurados (lunes y miércoles): al menos 1 slot por día, tope 3
    assert 2 <= len(data) <= 3, f"se esperaban 2-3 slots, se devolvieron {len(data)}"
    for slot in data:
        datetime.fromisoformat(slot["slot_datetime"])  # debe ser un ISO string válido

    # Cada slot debe caer en un día distinto
    days = {d["slot_datetime"][:10] for d in data}
    assert len(days) == len(data)
