import pytest
from datetime import time
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category_schedule import CategorySchedule, CategoryType, RotationType


@pytest.mark.asyncio
async def test_create_schedule_specialty(client: AsyncClient, test_db: AsyncSession):
    """Test creating a new specialty schedule."""
    response = await client.post(
        "/admin/schedules",
        json={
            "category_type": "specialty",
            "name": "Cardiology",
            "day_of_week": 0,  # Monday
            "start_time": "09:00:00",
            "turn_duration": 30,
            "max_turns_per_block": 4,
            "rotation_type": "fixed",
            "rotation_weeks": 1,
        },
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["category_type"] == "specialty"
    assert data["name"] == "Cardiology"
    assert data["day_of_week"] == 0
    assert data["start_time"] == "09:00:00"
    assert data["turn_duration"] == 30
    assert data["max_turns_per_block"] == 4
    assert data["rotation_type"] == "fixed"
    assert data["rotation_weeks"] == 1
    assert "id" in data


@pytest.mark.asyncio
async def test_create_schedule_laboratory(client: AsyncClient, test_db: AsyncSession):
    """Test creating a new laboratory schedule."""
    response = await client.post(
        "/admin/schedules",
        json={
            "category_type": "laboratory",
            "name": "Blood Test",
            "day_of_week": 2,  # Wednesday
            "start_time": "08:00:00",
            "turn_duration": 15,
            "max_turns_per_block": 8,
            "rotation_type": "alternated",
            "rotation_weeks": 2,
        },
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["category_type"] == "laboratory"
    assert data["name"] == "Blood Test"
    assert data["day_of_week"] == 2
    assert data["rotation_type"] == "alternated"
    assert data["rotation_weeks"] == 2


@pytest.mark.asyncio
async def test_update_existing_schedule(client: AsyncClient, test_db: AsyncSession):
    """Test updating an existing schedule (same category_type and day_of_week)."""
    # Create initial schedule
    initial_response = await client.post(
        "/admin/schedules",
        json={
            "category_type": "specialty",
            "name": "Neurology",
            "day_of_week": 1,  # Tuesday
            "start_time": "10:00:00",
            "turn_duration": 45,
            "max_turns_per_block": 3,
            "rotation_type": "fixed",
            "rotation_weeks": 1,
        },
    )
    assert initial_response.status_code == 201
    initial_data = initial_response.json()
    schedule_id = initial_data["id"]
    
    # Update with different values but same category_type and day_of_week
    update_response = await client.post(
        "/admin/schedules",
        json={
            "category_type": "specialty",
            "name": "Neurology Advanced",  # Updated name
            "day_of_week": 1,  # Same Tuesday
            "start_time": "14:00:00",  # Updated time
            "turn_duration": 60,  # Updated duration
            "max_turns_per_block": 5,  # Updated max turns
            "rotation_type": "alternated",  # Updated rotation
            "rotation_weeks": 2,  # Updated weeks
        },
    )
    
    assert update_response.status_code == 201
    updated_data = update_response.json()
    
    # Should have the same ID (updated, not created new)
    assert updated_data["id"] == schedule_id
    assert updated_data["name"] == "Neurology Advanced"
    assert updated_data["start_time"] == "14:00:00"
    assert updated_data["turn_duration"] == 60
    assert updated_data["max_turns_per_block"] == 5
    assert updated_data["rotation_type"] == "alternated"
    assert updated_data["rotation_weeks"] == 2


@pytest.mark.asyncio
async def test_different_category_types_same_day(client: AsyncClient, test_db: AsyncSession):
    """Test creating schedules for different category types on the same day."""
    # Create specialty schedule for Monday
    specialty_response = await client.post(
        "/admin/schedules",
        json={
            "category_type": "specialty",
            "name": "Dermatology",
            "day_of_week": 0,  # Monday
            "start_time": "09:00:00",
            "turn_duration": 30,
            "max_turns_per_block": 4,
            "rotation_type": "fixed",
            "rotation_weeks": 1,
        },
    )
    assert specialty_response.status_code == 201
    
    # Create laboratory schedule for Monday (different category_type)
    lab_response = await client.post(
        "/admin/schedules",
        json={
            "category_type": "laboratory",
            "name": "X-Ray",
            "day_of_week": 0,  # Monday (same day)
            "start_time": "08:00:00",
            "turn_duration": 20,
            "max_turns_per_block": 6,
            "rotation_type": "fixed",
            "rotation_weeks": 1,
        },
    )
    assert lab_response.status_code == 201
    
    # Both should exist independently
    specialty_data = specialty_response.json()
    lab_data = lab_response.json()
    assert specialty_data["id"] != lab_data["id"]
    assert specialty_data["category_type"] == "specialty"
    assert lab_data["category_type"] == "laboratory"


@pytest.mark.asyncio
async def test_list_schedules_empty(client: AsyncClient, test_db: AsyncSession):
    """Test listing schedules when none exist."""
    response = await client.get("/admin/schedules")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


@pytest.mark.asyncio
async def test_list_schedules_with_data(client: AsyncClient, test_db: AsyncSession):
    """Test listing all schedules."""
    # Create multiple schedules
    schedules_to_create = [
        {
            "category_type": "specialty",
            "name": "Cardiology",
            "day_of_week": 0,
            "start_time": "09:00:00",
            "turn_duration": 30,
            "max_turns_per_block": 4,
            "rotation_type": "fixed",
            "rotation_weeks": 1,
        },
        {
            "category_type": "specialty",
            "name": "Neurology",
            "day_of_week": 1,
            "start_time": "10:00:00",
            "turn_duration": 45,
            "max_turns_per_block": 3,
            "rotation_type": "fixed",
            "rotation_weeks": 1,
        },
        {
            "category_type": "laboratory",
            "name": "Blood Test",
            "day_of_week": 2,
            "start_time": "08:00:00",
            "turn_duration": 15,
            "max_turns_per_block": 8,
            "rotation_type": "alternated",
            "rotation_weeks": 2,
        },
    ]
    
    for schedule_data in schedules_to_create:
        create_response = await client.post("/admin/schedules", json=schedule_data)
        assert create_response.status_code == 201
    
    # List all schedules
    list_response = await client.get("/admin/schedules")
    
    assert list_response.status_code == 200
    data = list_response.json()
    assert isinstance(data, list)
    assert len(data) == 3
    
    # Verify ordering (by category_type, then day_of_week)
    # Laboratory comes before Specialty alphabetically
    assert data[0]["category_type"] == "laboratory"
    assert data[0]["day_of_week"] == 2
    assert data[1]["category_type"] == "specialty"
    assert data[1]["day_of_week"] == 0
    assert data[2]["category_type"] == "specialty"
    assert data[2]["day_of_week"] == 1


@pytest.mark.asyncio
async def test_create_schedule_invalid_day_of_week(client: AsyncClient):
    """Test creating schedule with invalid day_of_week."""
    response = await client.post(
        "/admin/schedules",
        json={
            "category_type": "specialty",
            "name": "Cardiology",
            "day_of_week": 7,  # Invalid (should be 0-6)
            "start_time": "09:00:00",
            "turn_duration": 30,
            "max_turns_per_block": 4,
            "rotation_type": "fixed",
            "rotation_weeks": 1,
        },
    )
    
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_create_schedule_invalid_turn_duration(client: AsyncClient):
    """Test creating schedule with invalid turn_duration."""
    response = await client.post(
        "/admin/schedules",
        json={
            "category_type": "specialty",
            "name": "Cardiology",
            "day_of_week": 0,
            "start_time": "09:00:00",
            "turn_duration": 0,  # Invalid (should be > 0)
            "max_turns_per_block": 4,
            "rotation_type": "fixed",
            "rotation_weeks": 1,
        },
    )
    
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_create_schedule_default_rotation_weeks(client: AsyncClient, test_db: AsyncSession):
    """Test creating schedule with default rotation_weeks."""
    response = await client.post(
        "/admin/schedules",
        json={
            "category_type": "specialty",
            "name": "Orthopedics",
            "day_of_week": 3,
            "start_time": "11:00:00",
            "turn_duration": 40,
            "max_turns_per_block": 5,
            "rotation_type": "fixed",
            # rotation_weeks not specified, should default to 1
        },
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["rotation_weeks"] == 1  # Default value
