from fastapi.testclient import TestClient

from backend.app.main import app


def test_health_is_process_liveness() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["X-Correlation-ID"]


def test_ready_reports_dependency_state() -> None:
    with TestClient(app) as client:
        response = client.get("/ready", headers={"X-Correlation-ID": "test-correlation"})

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["dependencies"] == {"database": True, "pgvector": True}
    assert response.headers["X-Correlation-ID"] == "test-correlation"


def test_openapi_metadata_is_available() -> None:
    with TestClient(app) as client:
        response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["title"] == "HR Talent Matching Platform API"
