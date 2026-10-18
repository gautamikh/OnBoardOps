import pytest
from fastapi.testclient import TestClient

import app.mcp_workflow as workflow
from app.main import app
from app.mcp_client import (
    EmployeeNotFound,
    EmployeeRecord,
    MCPUnavailable,
)


PAYLOAD = {
    "employee_id": "EMP-001",
    "job_title": "Backend Engineer",
    "start_date": "2026-11-02",
}


def test_plan_uses_employee_directory_details(monkeypatch):
    async def fake_lookup(employee_id):
        assert employee_id == "EMP-001"

        return EmployeeRecord(
            employee_id=employee_id,
            name="Maya Example",
            department="Engineering",
            location="Berlin",
            manager="Sam Example",
        )

    monkeypatch.setattr(workflow, "lookup_employee", fake_lookup)

    with TestClient(app) as client:
        response = client.post("/plans/from-employee", json=PAYLOAD)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["request"]["employee_name"] == "Maya Example"
    assert body["request"]["location"] == "Berlin"
    assert len(body["tasks"]) == 3
    assert all("Maya Example" in task["title"] for task in body["tasks"])


@pytest.mark.parametrize(
    "error, expected_status",
    [
        (EmployeeNotFound, 404),
        (MCPUnavailable, 503),
    ],
)
def test_lookup_failure_returns_no_plan(monkeypatch, error, expected_status):
    async def failed_lookup(employee_id):
        raise error("Simulated lookup failure")

    monkeypatch.setattr(workflow, "lookup_employee", failed_lookup)

    with TestClient(app) as client:
        response = client.post("/plans/from-employee", json=PAYLOAD)

    assert response.status_code == expected_status
    assert "tasks" not in response.json()