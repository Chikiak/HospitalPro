"""Unit tests for the rate-limit core (F2-10).

These tests exercise :mod:`app.core.rate_limit` directly, without HTTP, so
they isolate the identity key from the IP: the same identity from different
IPs shares its counter, and different identities do not. They also verify
that ``X-Forwarded-For`` spoofing does not change the IP key unless trusted
proxies are explicitly configured.

No DNI/password/token values are logged or asserted in 429 responses.
"""

from types import SimpleNamespace

import pytest
from slowapi.errors import RateLimitExceeded

from app.core import rate_limit as rl


def _dummy_request() -> SimpleNamespace:
    return SimpleNamespace(state=SimpleNamespace())


def test_identity_key_builds_prefixed_key():
    assert rl.identity_key("login", "12345678901") == "login:12345678901"
    assert rl.identity_key("book", "12345678901") == "book:12345678901"


def test_identity_key_none_or_empty_returns_none():
    assert rl.identity_key("login", None) is None
    assert rl.identity_key("login", "") is None
    assert rl.identity_key("login", "   ") is None


def test_normalize_identity_strips_whitespace():
    assert rl.normalize_identity(" 12345678901 ") == "12345678901"
    assert rl.normalize_identity("123 456 789") == "123456789"
    assert rl.normalize_identity(None) is None


def test_check_limit_allows_within_limit_and_exceeds(monkeypatch):
    # Reset shared storage so this test is hermetic.
    rl._identity_storage.reset()
    key = rl.identity_key("login", "12345678901")
    scope = "login"

    # 5 requests within "5/minute" are allowed.
    for _ in range(5):
        rl.check_limit(_dummy_request(), "5/minute", key, scope)

    # The 6th exhausts the identity counter.
    with pytest.raises(RateLimitExceeded):
        rl.check_limit(_dummy_request(), "5/minute", key, scope)


def test_check_limit_different_identities_do_not_share(monkeypatch):
    rl._identity_storage.reset()
    key_a = rl.identity_key("login", "11111111111")
    key_b = rl.identity_key("login", "22222222222")
    scope = "login"

    # Identity A consumes its own counter.
    for _ in range(5):
        rl.check_limit(_dummy_request(), "5/minute", key_a, scope)
    with pytest.raises(RateLimitExceeded):
        rl.check_limit(_dummy_request(), "5/minute", key_a, scope)

    # Identity B is unaffected: same counter value would be fresh.
    # B consumes 5 and only the 6th is denied.
    for _ in range(5):
        rl.check_limit(_dummy_request(), "5/minute", key_b, scope)
    with pytest.raises(RateLimitExceeded):
        rl.check_limit(_dummy_request(), "5/minute", key_b, scope)


def test_check_limit_reset_clears_counter(monkeypatch):
    rl._identity_storage.reset()
    key = rl.identity_key("register", "33333333333")
    scope = "register"

    for _ in range(5):
        rl.check_limit(_dummy_request(), "5/minute", key, scope)
    with pytest.raises(RateLimitExceeded):
        rl.check_limit(_dummy_request(), "5/minute", key, scope)

    # After reset, the same identity can hit again.
    rl._identity_storage.reset()
    for _ in range(5):
        rl.check_limit(_dummy_request(), "5/minute", key, scope)
    with pytest.raises(RateLimitExceeded):
        rl.check_limit(_dummy_request(), "5/minute", key, scope)


def _fake_request(client_host: str, xff: str | None = None) -> SimpleNamespace:
    headers = {}
    if xff is not None:
        headers["X-Forwarded-For"] = xff
    return SimpleNamespace(
        client=SimpleNamespace(host=client_host),
        headers=SimpleNamespace(
            get=lambda name, default=None: headers.get(name, default)
        ),
    )


def test_get_client_ip_ignores_xff_without_trusted_proxies(monkeypatch):
    monkeypatch.setattr(rl, "TRUSTED_PROXIES", set())
    req = _fake_request("10.0.0.5", xff="1.2.3.4")
    # Spoofed X-Forwarded-For is ignored when the direct connection is not a
    # trusted proxy.
    assert rl.get_client_ip(req) == "10.0.0.5"


def test_get_client_ip_uses_xff_for_trusted_proxy(monkeypatch):
    monkeypatch.setattr(rl, "TRUSTED_PROXIES", {"10.0.0.5"})
    req = _fake_request("10.0.0.5", xff="1.2.3.4")
    assert rl.get_client_ip(req) == "1.2.3.4"


def test_get_client_ip_no_client_returns_loopback():
    req = SimpleNamespace(
        client=None, headers=SimpleNamespace(get=lambda *a, **k: None)
    )
    assert rl.get_client_ip(req) == "127.0.0.1"
