from fastapi.testclient import TestClient

import devsecops_ai
from devsecops_ai.app import create_app


def test_health_returns_ok() -> None:
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_reports_package_version() -> None:
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.json()["version"] == devsecops_ai.__version__


def test_health_response_shape() -> None:
    client = TestClient(create_app())

    response = client.get("/health")

    assert set(response.json().keys()) == {"status", "version"}


def test_create_app_returns_independent_instances() -> None:
    first_app = create_app()
    second_app = create_app()

    assert first_app is not second_app
