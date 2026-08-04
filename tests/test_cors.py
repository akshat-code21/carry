"""Unit tests for CORS configuration."""

from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_cors_preflight_allowed_origin():
    response = client.options(
        "/health",
        headers={
            "Origin": "https://carry-fin.vercel.app",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "https://carry-fin.vercel.app"
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_preflight_vercel_preview():
    response = client.options(
        "/health",
        headers={
            "Origin": "https://carry-fin-git-main-akshat.vercel.app",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "https://carry-fin-git-main-akshat.vercel.app"
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_preflight_localhost():
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
