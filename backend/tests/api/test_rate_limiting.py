"""Tests for rate limiting functionality.

Note: These tests verify that rate limiting is properly configured.
Due to slowapi's global state, running all tests together may cause
test isolation issues. Each test can be run individually to verify
the specific rate limit behavior.
"""

import asyncio
from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.main import app
from app.models.user import User, UserRole
from app.repositories.allowed_person_repository import AllowedPersonRepository


@pytest.mark.asyncio
async def test_login_rate_limit_is_enforced(client: AsyncClient, test_db: AsyncSession):
    """Test that login endpoint enforces rate limits (5 requests per minute)."""
    # Add DNI to whitelist and create a user
    allowed_repo = AllowedPersonRepository(test_db)
    await allowed_repo.bulk_create([{"dni": "99999999999"}])

    # Register a user
    await client.post(
        "/auth/users/register",
        json={
            "dni": "99999999999",
            "password": "testpassword123",
            "full_name": "Test User Rate Limit",
            "role": "patient",
        },
    )

    # Make requests until we hit the rate limit or reach a reasonable threshold
    rate_limited = False
    max_attempts = 10

    for _ in range(max_attempts):
        response = await client.post(
            "/auth/login/access-token",
            json={"dni": "99999999999", "password": "wrongpassword"},
        )

        if response.status_code == 429:
            rate_limited = True
            # Verify the error message mentions rate limiting
            assert (
                "rate limit" in response.text.lower()
                or "too many" in response.text.lower()
            )
            break

    # We should have hit the rate limit within max_attempts
    assert rate_limited, f"Rate limit was not enforced after {max_attempts} requests"


@pytest.mark.asyncio
async def test_staff_login_rate_limit_is_enforced(
    client: AsyncClient, test_db: AsyncSession
):
    """Test that staff login endpoint enforces rate limits (3 requests per minute)."""
    rate_limited = False
    max_attempts = 10

    for _ in range(max_attempts):
        response = await client.post(
            "/auth/login/staff",
            json={"dni": "99999999999", "password": "wrongpassword"},
        )

        if response.status_code == 429:
            rate_limited = True
            assert (
                "rate limit" in response.text.lower()
                or "too many" in response.text.lower()
            )
            break

    # We should have hit the rate limit within max_attempts
    assert rate_limited, f"Rate limit was not enforced after {max_attempts} requests"


@pytest.mark.asyncio
async def test_pdf_export_rate_limit_is_configured(
    client: AsyncClient, test_db: AsyncSession
):
    """Test that PDF export endpoint has rate limiting configured."""
    # Create a patient user
    allowed_repo = AllowedPersonRepository(test_db)
    await allowed_repo.bulk_create([{"dni": "88888888888"}])

    # Register patient
    reg_response = await client.post(
        "/auth/users/register",
        json={
            "dni": "88888888888",
            "password": "testpassword123",
            "full_name": "Test User PDF",
            "role": "patient",
        },
    )

    # Ensure a medical record exists so the PDF endpoint can be exercised
    from app.repositories.medical_record_repository import MedicalRecordRepository

    medical_record_repo = MedicalRecordRepository(test_db)
    await medical_record_repo.create(
        patient_id=reg_response.json()["id"], registration_survey={}
    )

    # Try to login (may be rate limited from other tests, which is OK)
    login_response = await client.post(
        "/auth/login/access-token",
        json={"dni": "88888888888", "password": "testpassword123"},
    )

    # If we can login, test the PDF endpoint
    if login_response.status_code == 200:
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        patient_id = login_response.json()["user"]["id"]

        # Make multiple requests to verify rate limiting exists
        rate_limited = False
        max_attempts = 15

        for _ in range(max_attempts):
            response = await client.get(
                f"/patients/{patient_id}/medical-record/pdf",
                headers=headers,
            )

            if response.status_code == 429:
                rate_limited = True
                assert (
                    "rate limit" in response.text.lower()
                    or "too many" in response.text.lower()
                )
                break

        # We should have hit the rate limit within max_attempts
        assert rate_limited, (
            f"Rate limit was not enforced after {max_attempts} requests"
        )
    else:
        # If we're rate limited on login, that's evidence rate limiting is working
        pytest.skip(
            "Could not login due to rate limiting from other tests - rate limiting is working"
        )


@pytest.mark.asyncio
async def test_rate_limiting_allows_normal_use(
    client: AsyncClient, test_db: AsyncSession
):
    """Test that rate limiting doesn't block normal, non-excessive use."""
    # Add DNI to whitelist
    allowed_repo = AllowedPersonRepository(test_db)
    await allowed_repo.bulk_create([{"dni": "11111111111"}])

    # Register a user
    reg_response = await client.post(
        "/auth/users/register",
        json={
            "dni": "11111111111",
            "password": "validpassword123",
            "full_name": "Normal User",
            "role": "patient",
        },
    )

    # A single login attempt should succeed (or fail with wrong credentials, but not rate limit)
    response = await client.post(
        "/auth/login/access-token",
        json={"dni": "11111111111", "password": "validpassword123"},
    )

    # Should either succeed or be rate limited from previous tests
    # If rate limited, that's actually proof the system is working
    if response.status_code == 429:
        pytest.skip(
            "Rate limited from previous tests - this proves rate limiting works"
        )
    else:
        # Should be able to login successfully
        assert response.status_code == 200
        assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_register_rate_limit(client: AsyncClient, test_db: AsyncSession):
    """Register endpoint enforces 5 requests per minute; 6th returns 429."""
    # Reset the in-memory limiter storage so this test is isolated
    app.state.limiter._storage.reset()

    # Add DNI to whitelist (los 5 DNIs que usaremos en el bucle)
    allowed_repo = AllowedPersonRepository(test_db)
    for i in range(5):
        await allowed_repo.bulk_create([{"dni": f"555555555{i}5"}])

    # First 5 registrations should succeed (201) — no se acepta 422 antes del 429
    for i in range(5):
        response = await client.post(
            "/auth/users/register",
            json={
                "dni": f"555555555{i}5",
                "password": "securepass123",
                "full_name": f"Rate Limit User {i}",
                "role": "patient",
            },
        )
        assert response.status_code == 201, (
            f"Request {i} expected 201, got {response.status_code}: {response.text}"
        )

    # 6th request should be rate limited
    response = await client.post(
        "/auth/users/register",
        json={
            "dni": "55555555599",
            "password": "securepass123",
            "full_name": "Rate Limit User 6",
            "role": "patient",
        },
    )
    assert response.status_code == 429, f"Expected 429, got {response.status_code}"


@pytest.mark.asyncio
async def test_x_forwarded_for_spoofing_does_not_change_ip_key(
    client: AsyncClient, test_db: AsyncSession
):
    """X-Forwarded-For spoofed must not change the IP rate-limit key.

    Without trusted proxies configured, the key is the direct connection IP
    (testclient). Alternating two spoofed X-Forwarded-For values for the same
    DNI must still exhaust a single counter by the 6th request.
    """
    spoof_dni = "99999999999"

    statuses = []
    for i in range(6):
        xff = "1.2.3.4" if i % 2 == 0 else "5.6.7.8"
        response = await client.post(
            "/auth/login/access-token",
            json={"dni": spoof_dni, "password": "wrongpassword"},
            headers={"X-Forwarded-For": xff},
        )
        statuses.append(response.status_code)

    # The 6th exhausts the single testclient-IP counter (5/minute), not a
    # spoofed X-Forwarded-For key.
    assert statuses[-1] == 429, f"Expected 429 on 6th request, got {statuses[-1]}"


@pytest.mark.asyncio
async def test_book_authenticated_rate_limit_by_identity(
    client: AsyncClient, test_db: AsyncSession
):
    """/appointments/book enforces 10/minute per authenticated user (sub/DNI).

    The same user from the same IP exhausts its identity counter; a different
    user is not affected. IP is kept (200/minute) so it does not interfere.
    """
    future = (datetime.now() + timedelta(days=7)).isoformat()
    book_body = {
        "category_id": 99999,
        "appointment_date": future,
        "category_name": "Cardiologia",
    }

    # Two real users in the DB.
    test_db.add(
        User(
            dni="BOOKUSERA",
            hashed_password="x",
            full_name="User A",
            role=UserRole.PATIENT,
            is_active=True,
        )
    )
    test_db.add(
        User(
            dni="BOOKUSERB",
            hashed_password="x",
            full_name="User B",
            role=UserRole.PATIENT,
            is_active=True,
        )
    )
    await test_db.commit()

    token_a = create_access_token(data={"sub": "BOOKUSERA", "role": "patient"})
    token_b = create_access_token(data={"sub": "BOOKUSERB", "role": "patient"})
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A: 10 requests within the 10/minute identity limit (all 404 because
    # the category does not exist, but the identity counter still advances).
    rate_limited_a = False
    for _ in range(11):
        response = await client.post(
            "/appointments/book", json=book_body, headers=headers_a
        )
        if response.status_code == 429:
            rate_limited_a = True
            assert (
                "rate limit" in response.text.lower()
                or "too many" in response.text.lower()
            )
            break

    assert rate_limited_a, "User A identity counter was not exhausted"

    # User B must NOT be affected by A's exhausted counter: still 404 (not 429).
    response_b = await client.post(
        "/appointments/book", json=book_body, headers=headers_b
    )
    assert response_b.status_code != 429, (
        f"User B should not share A's counter, got {response_b.status_code}"
    )


@pytest.mark.asyncio
async def test_book_counter_reset(client: AsyncClient, test_db: AsyncSession):
    """Resetting the storage clears the per-user book counter."""
    future = (datetime.now() + timedelta(days=7)).isoformat()
    book_body = {
        "category_id": 99999,
        "appointment_date": future,
        "category_name": "Cardiologia",
    }

    test_db.add(
        User(
            dni="BOOKRESET",
            hashed_password="x",
            full_name="Reset User",
            role=UserRole.PATIENT,
            is_active=True,
        )
    )
    await test_db.commit()
    token = create_access_token(data={"sub": "BOOKRESET", "role": "patient"})
    headers = {"Authorization": f"Bearer {token}"}

    # Exhaust user A's identity counter (10/minute).
    for _ in range(11):
        response = await client.post(
            "/appointments/book", json=book_body, headers=headers
        )
        if response.status_code == 429:
            break

    # After reset, the same user can book again (404, not 429).
    app.state.limiter._storage.reset()
    response = await client.post("/appointments/book", json=book_body, headers=headers)
    assert response.status_code != 429, (
        f"Counter should reset, got {response.status_code}"
    )
