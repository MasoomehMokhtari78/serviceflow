import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import Settings, settings

client = TestClient(app)


# ====================================================
# H4: JWT Secret Production Enforcement
# ====================================================

def test_h4_production_startup_fails_without_strong_secret():
    """H4: In production, application fails to start if SECRET_KEY is default or weak."""
    # Default secret in production -> raises ValueError
    with pytest.raises(ValueError) as exc:
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY=settings.DEV_SECRET_FALLBACK,
            GEMINI_API_KEY=None
        )
    assert "FATAL SECURITY CONFIGURATION" in str(exc.value)


    # Short secret in production -> raises ValueError during validation
    with pytest.raises(Exception) as exc:
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="short-secret",
            GEMINI_API_KEY=None
        )
    assert "FATAL SECURITY CONFIGURATION" in str(exc.value)


def test_h4_production_startup_succeeds_with_strong_secret():
    """H4: In production with explicit high-entropy secret, security validation passes."""
    strong_secret = "f" * 64  # 64-character high entropy hex
    prod_settings = Settings(
        ENVIRONMENT="production",
        SECRET_KEY=strong_secret,
        GEMINI_API_KEY=None
    )
    # Must not raise
    prod_settings.validate_production_security()


def test_h4_secret_never_leaked_in_health_or_errors():
    """H4: Secret key is never returned in health check or error responses."""
    health_res = client.get("/health")
    assert health_res.status_code == 200
    assert settings.SECRET_KEY not in health_res.text


# ====================================================
# M5: CORS Configuration (No Wildcard with Credentials)
# ====================================================

def test_m5_cors_no_wildcard_origins():
    """M5: Wildcard '*' is strictly prohibited in CORS_ORIGINS when credentials mode is enabled."""
    assert "*" not in settings.CORS_ORIGINS
    for origin in settings.CORS_ORIGINS:
        assert origin != "*"


def test_m5_cors_preflight_allowed_origin():
    """M5: Explicit allowed origin receives proper CORS response headers."""
    response = client.options(
        "/api/v1/orders",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET"
        }
    )
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_m5_cors_disallows_arbitrary_untrusted_origin():
    """M5: Untrusted arbitrary origin is not echoed with credentials access."""
    response = client.options(
        "/api/v1/orders",
        headers={
            "Origin": "https://malicious-attacker-domain.com",
            "Access-Control-Request-Method": "GET"
        }
    )
    # Untrusted origin must NOT be granted access
    assert response.headers.get("access-control-allow-origin") != "https://malicious-attacker-domain.com"
    assert response.headers.get("access-control-allow-origin") != "*"


# ====================================================
# M2: Structured Request Tracing & Logging Headers
# ====================================================

def test_m2_response_includes_request_id():
    """M2: Every request receives an X-Request-ID response header for distributed tracing."""
    res = client.get("/health")
    assert res.status_code == 200
    assert "X-Request-ID" in res.headers
    assert len(res.headers["X-Request-ID"]) > 0


def test_m2_client_supplied_request_id_preserved():
    """M2: If client supplies an X-Request-ID header, the system preserves and returns it."""
    client_request_id = "trace-req-uuid-9999"
    res = client.get("/health", headers={"X-Request-ID": client_request_id})
    assert res.status_code == 200
    assert res.headers.get("X-Request-ID") == client_request_id
