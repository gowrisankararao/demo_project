from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_db, None)
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_create_alert(client: TestClient) -> None:
    payload = {
        "title": "High CPU usage",
        "severity": "critical",
        "source": "api-server",
        "metric_name": "cpu_usage",
        "metric_value": 95.0,
        "threshold": 80.0,
    }

    response = client.post("/alerts/", json=payload)

    assert response.status_code == 201
    assert response.json()["title"] == payload["title"]
    assert response.json()["severity"] == payload["severity"]
    assert response.json()["id"] > 0


def test_list_alerts(client: TestClient) -> None:
    titles = ["High CPU usage", "Low disk space"]
    for title in titles:
        client.post(
            "/alerts/",
            json={
                "title": title,
                "severity": "warning",
                "source": "monitor",
                "metric_name": "resource_usage",
                "metric_value": 85.0,
                "threshold": 80.0,
            },
        )

    response = client.get("/alerts/")

    assert response.status_code == 200
    assert [alert["title"] for alert in response.json()] == titles


def test_get_alert_by_id(client: TestClient) -> None:
    create_response = client.post(
        "/alerts/",
        json={
            "title": "High memory usage",
            "severity": "warning",
            "source": "worker",
            "metric_name": "memory_usage",
            "metric_value": 90.0,
            "threshold": 75.0,
        },
    )
    alert_id = create_response.json()["id"]

    response = client.get(f"/alerts/{alert_id}")

    assert response.status_code == 200
    assert response.json()["id"] == alert_id
    assert response.json()["metric_name"] == "memory_usage"


def test_explain_alert(client: TestClient) -> None:
    create_response = client.post(
        "/alerts/",
        json={
            "title": "High latency",
            "severity": "critical",
            "source": "gateway",
            "metric_name": "request_latency",
            "metric_value": 250.0,
            "threshold": 150.0,
        },
    )
    alert = create_response.json()

    response = client.post(f"/alerts/{alert['id']}/explain")

    assert response.status_code == 200
    result = response.json()
    assert result["alert_id"] == alert["id"]
    assert alert["severity"] in result["explanation"]
    assert alert["metric_name"] in result["explanation"]
    assert datetime.fromisoformat(result["generated_at"].replace("Z", "+00:00"))


def _create_alert(client: TestClient, **overrides: str | float) -> dict:
    payload: dict[str, str | float] = {
        "title": "Test alert",
        "severity": "warning",
        "source": "test-source",
        "metric_name": "test_metric",
        "metric_value": 50.0,
        "threshold": 40.0,
    }
    payload.update(overrides)
    response = client.post("/alerts/", json=payload)
    assert response.status_code == 201
    return response.json()


def test_explain_alert_for_nonexistent_id_returns_404(client: TestClient) -> None:
    response = client.post("/alerts/999/explain")

    assert response.status_code == 404
    assert response.json()["detail"] == "Alert not found"


def test_explain_alert_when_metric_is_below_threshold(client: TestClient) -> None:
    alert = _create_alert(
        client,
        title="Connection pool below minimum",
        severity="warning",
        source="db-pool",
        metric_name="active_connections",
        metric_value=2,
        threshold=10,
    )

    response = client.post(f"/alerts/{alert['id']}/explain")

    assert response.status_code == 200
    assert "fell below its threshold" in response.json()["explanation"]


def test_explain_alert_with_zero_threshold_does_not_crash(client: TestClient) -> None:
    alert = _create_alert(
        client,
        title="Unexpected traffic on idle endpoint",
        severity="info",
        source="edge-cache",
        metric_name="request_count",
        metric_value=5,
        threshold=0,
    )

    response = client.post(f"/alerts/{alert['id']}/explain")

    assert response.status_code == 200
    assert "threshold of 0.0" in response.json()["explanation"]


def test_explain_alert_acknowledgement_defaults_when_unresolved(
    client: TestClient,
) -> None:
    alert = _create_alert(client, severity="critical")

    response = client.post(f"/alerts/{alert['id']}/explain")

    assert response.status_code == 200
    assert response.json()["explanation"].endswith(
        "Acknowledged by: Not yet acknowledged."
    )