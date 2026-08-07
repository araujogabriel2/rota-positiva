from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def test_health_check_returns_api_status() -> None:
    client = TestClient(create_app(Settings()))

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "application": "Rota Positiva API",
        "api_version": "v1",
    }


def test_cors_accepts_configured_frontend() -> None:
    settings = Settings(cors_origins="http://localhost:5173")
    client = TestClient(create_app(settings))

    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_cors_rejects_unknown_origin() -> None:
    settings = Settings(cors_origins="http://localhost:5173")
    client = TestClient(create_app(settings))

    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "https://site-nao-autorizado.example",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
