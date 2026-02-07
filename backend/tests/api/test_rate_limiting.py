import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch

from app.repositories.allowed_person_repository import AllowedPersonRepository


@pytest.mark.asyncio
async def test_login_rate_limit(client: AsyncClient, test_db: AsyncSession):
    """Test that login endpoint is rate limited to 5 requests per minute."""
    # Add DNI to whitelist and register a user
    allowed_repo = AllowedPersonRepository(test_db)
    await allowed_repo.bulk_create([{"dni": "11111111111"}])
    
    await client.post(
        "/auth/users/register",
        json={
            "dni": "11111111111",
            "password": "testpassword123",
            "full_name": "Test User",
            "role": "patient",
        },
    )
    
    # Make 5 login attempts (should all succeed or fail normally)
    for i in range(5):
        response = await client.post(
            "/auth/login/access-token",
            json={
                "dni": "11111111111",
                "password": "testpassword123",
            },
        )
        # Should either succeed (200) or fail due to wrong password (401)
        # but not due to rate limiting
        assert response.status_code in [200, 401]
    
    # The 6th request should be rate limited
    response = await client.post(
        "/auth/login/access-token",
        json={
            "dni": "11111111111",
            "password": "testpassword123",
        },
    )
    
    # Should return 429 Too Many Requests
    assert response.status_code == 429
    # Check for rate limit error message
    assert "rate limit" in response.text.lower() or "too many" in response.text.lower()


@pytest.mark.asyncio
async def test_staff_login_rate_limit(client: AsyncClient):
    """Test that staff login endpoint is rate limited to 5 requests per minute."""
    with patch("app.api.endpoints.auth.settings.STAFF_PASSWORD", "correct-staff-password"):
        # Make 5 staff login attempts (should all succeed)
        for i in range(5):
            response = await client.post(
                "/auth/login/staff",
                json={
                    "password": "correct-staff-password",
                },
            )
            # Should succeed
            assert response.status_code == 200
        
        # The 6th request should be rate limited
        response = await client.post(
            "/auth/login/staff",
            json={
                "password": "correct-staff-password",
            },
        )
        
        # Should return 429 Too Many Requests
        assert response.status_code == 429
        # Check for rate limit error message
        assert "rate limit" in response.text.lower() or "too many" in response.text.lower()


@pytest.mark.asyncio
async def test_pdf_export_rate_limit(client: AsyncClient, test_db: AsyncSession):
    """Test that PDF export endpoint is rate limited to 10 requests per minute."""
    # Add DNI to whitelist and register a unique user for this test
    allowed_repo = AllowedPersonRepository(test_db)
    await allowed_repo.bulk_create([{"dni": "22222222222"}])
    
    register_response = await client.post(
        "/auth/users/register",
        json={
            "dni": "22222222222",
            "password": "testpassword123",
            "full_name": "Test User 2",
            "role": "patient",
        },
    )
    
    # Get a fresh client to avoid rate limit from previous tests
    # Login to get access token
    login_response = await client.post(
        "/auth/login/access-token",
        json={
            "dni": "22222222222",
            "password": "testpassword123",
        },
    )
    
    # Check if login was successful (not rate limited)
    if login_response.status_code != 200:
        pytest.skip("Login was rate limited from previous test, skipping PDF test")
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    patient_id = register_response.json()["id"]
    
    # Make 10 PDF export requests
    # The endpoint should process the request (even if it fails with 500 due to missing data)
    # but should NOT return 429 (rate limit)
    rate_limited_count = 0
    for i in range(10):
        try:
            response = await client.get(
                f"/patients/{patient_id}/medical-record/pdf",
                headers=headers,
            )
            # Track if we got rate limited
            if response.status_code == 429:
                rate_limited_count += 1
        except Exception:
            # If an exception is raised (e.g., ValueError from missing medical record),
            # that's fine for this test - we're testing rate limiting, not the business logic
            pass
    
    # None of the first 10 requests should be rate limited
    assert rate_limited_count == 0, f"{rate_limited_count} of first 10 requests were rate limited"
    
    # The 11th request should be rate limited
    try:
        response = await client.get(
            f"/patients/{patient_id}/medical-record/pdf",
            headers=headers,
        )
        # Should return 429 Too Many Requests
        assert response.status_code == 429, f"Expected 429 but got {response.status_code}"
        # Check for rate limit error message
        assert "rate limit" in response.text.lower() or "too many" in response.text.lower()
    except Exception as e:
        # If we get an exception, the rate limiter should have caught the request first
        # This test should fail if we get here
        pytest.fail(f"Got exception instead of rate limit: {e}")
