import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository


@pytest.mark.asyncio
async def test_user_role_enum_has_staff(test_db: AsyncSession):
    """Test that UserRole enum includes STAFF role."""
    assert hasattr(UserRole, "STAFF")
    assert UserRole.STAFF.value == "staff"
    assert UserRole.STAFF in list(UserRole)


@pytest.mark.asyncio
async def test_create_user_with_staff_role(test_db: AsyncSession):
    """Test creating a user with STAFF role."""
    user_repo = UserRepository(test_db)
    
    user = await user_repo.create(
        dni="12345678901",
        hashed_password="hashed_test_password",
        full_name="Test Staff User",
        role=UserRole.STAFF,
    )
    
    assert user.id is not None
    assert user.dni == "12345678901"
    assert user.full_name == "Test Staff User"
    assert user.role == UserRole.STAFF
    assert user.role.value == "staff"
    assert user.is_active is True


@pytest.mark.asyncio
async def test_user_dni_is_unique_indexed_notnull(test_db: AsyncSession):
    """Test that DNI field has correct constraints (unique, indexed, not null)."""
    # Get the User table metadata
    user_table = User.__table__
    dni_column = user_table.c.dni
    
    # Check that dni column exists and has correct properties
    assert dni_column is not None
    assert dni_column.nullable is False  # not null constraint
    assert dni_column.unique is True  # unique constraint
    assert dni_column.index is True  # indexed


@pytest.mark.asyncio
async def test_all_user_roles_available(test_db: AsyncSession):
    """Test that all expected user roles are available."""
    expected_roles = {"PATIENT", "DOCTOR", "ADMIN", "STAFF"}
    actual_roles = {role.name for role in UserRole}
    
    assert actual_roles == expected_roles
    
    # Verify values
    assert UserRole.PATIENT.value == "patient"
    assert UserRole.DOCTOR.value == "doctor"
    assert UserRole.ADMIN.value == "admin"
    assert UserRole.STAFF.value == "staff"
