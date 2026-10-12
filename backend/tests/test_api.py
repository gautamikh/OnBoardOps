from unittest.mock import MagicMock
from uuid import UUID

import psycopg
import pytest
from fastapi.testclient import TestClient

import app.main as main
import app.onboarding as onboarding


PAYLOAD = {
    "employee_name": "Maya Example",
    "job_title": "Backend Engineer",
    "department": "Engineering",
    "location": "Berlin",
    "start_date": "2026-11-02",
}

REQUEST_ID = "12345678-1234-4234-8234-123456789abc"

SAVED_REQUEST = {
    **PAYLOAD,
    "id": REQUEST_ID,
    "status": "submitted",
    "created_at": "2026-10-10T12:00:00Z",
}


@pytest.fixture
def client(monkeypatch):
    def unexpected_database_call():
        raise AssertionError("This test must explicitly configure its database")

    monkeypatch.setattr(main, "get_connection", unexpected_database_call)
    monkeypatch.setattr(onboarding, "get_connection", unexpected_database_call)

    with TestClient(main.app) as test_client:
        yield test_client


def mock_database(monkeypatch, result):
    connection = MagicMock()
    cursor = (
        connection.__enter__.return_value
        .cursor.return_value.__enter__.return_value
    )
    cursor.fetchone.return_value = result

    monkeypatch.setattr(onboarding, "get_connection", lambda: connection)
    return cursor


def test_health_does_not_need_database(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.parametrize(
    "changes",
    [
        {"employee_name": "   "},
        {"start_date": "not-a-date"},
        {"department": ""},
        {"status": "approved"},
    ],
)
def test_invalid_request_is_rejected_before_database_access(client, changes):
    response = client.post(
        "/onboarding-requests",
        json={**PAYLOAD, **changes},
    )

    assert response.status_code == 422


def test_create_request(client, monkeypatch):
    cursor = mock_database(monkeypatch, None)

    def return_inserted_row():
        parameters = cursor.execute.call_args.args[1]
        return {**SAVED_REQUEST, "id": parameters[0]}

    cursor.fetchone.side_effect = return_inserted_row

    response = client.post("/onboarding-requests", json=PAYLOAD)

    assert response.status_code == 201
    body = response.json()
    assert UUID(body["id"]).version == 4
    assert body["status"] == "submitted"
    assert body["employee_name"] == PAYLOAD["employee_name"]


def test_get_existing_request(client, monkeypatch):
    mock_database(monkeypatch, SAVED_REQUEST)

    response = client.get(f"/onboarding-requests/{REQUEST_ID}")

    assert response.status_code == 200
    assert response.json()["id"] == REQUEST_ID
    assert response.json()["employee_name"] == PAYLOAD["employee_name"]


def test_get_missing_request(client, monkeypatch):
    mock_database(monkeypatch, None)

    response = client.get(f"/onboarding-requests/{REQUEST_ID}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Onboarding request not found"


@pytest.mark.parametrize("operation", ["create", "read", "ready"])
def test_database_failure_returns_safe_error(client, monkeypatch, operation):
    def database_unavailable():
        raise psycopg.OperationalError("private connection details")

    monkeypatch.setattr(onboarding, "get_connection", database_unavailable)
    monkeypatch.setattr(main, "get_connection", database_unavailable)

    if operation == "create":
        response = client.post("/onboarding-requests", json=PAYLOAD)
    elif operation == "read":
        response = client.get(f"/onboarding-requests/{REQUEST_ID}")
    else:
        response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}
    assert "private connection details" not in response.text