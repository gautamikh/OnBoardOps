import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.database import get_connection
from app.main import app


pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_INTEGRATION_TESTS") != "1",
    reason="Requires the isolated integration test database",
)


@pytest.fixture
def client():
    # Guard against accidentally targeting the development database.
    assert os.environ["DB_NAME"] == "onboardops_test"
    assert os.environ["DB_HOST"] == "db-test"

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def request_id(client):
    response = client.post(
        "/onboarding-requests",
        json={
            "employee_name": "Integration Test Employee",
            "job_title": "Backend Engineer",
            "department": "Engineering",
            "location": "Berlin",
            "start_date": "2026-11-02",
        },
    )

    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_plan_is_saved_and_reused(client, request_id):
    url = f"/onboarding-requests/{request_id}/plan"

    # A request initially has no plan.
    assert client.get(url).status_code == 404

    first = client.post(url)
    assert first.status_code == 201, first.text
    original = first.json()

    assert original["request_id"] == request_id
    assert original["status"] == "draft"
    assert len(original["tasks"]) == 3

    # A retry must return the same complete plan.
    second = client.post(url)
    assert second.status_code == 200, second.text
    assert second.json() == original

    retrieved = client.get(url)
    assert retrieved.status_code == 200
    assert retrieved.json() == original

    # Independently verify the record in PostgreSQL.
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, tasks FROM onboarding_plans
            WHERE request_id = %s
            """,
            (request_id,),
        ).fetchall()

    assert len(rows) == 1
    assert str(rows[0][0]) == original["id"]
    assert rows[0][1] == original["tasks"]


def test_unknown_request_cannot_get_a_plan(client):
    unknown_id = str(uuid4())

    response = client.post(
        f"/onboarding-requests/{unknown_id}/plan"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Onboarding request not found"

    with get_connection() as connection:
        count = connection.execute(
            """
            SELECT COUNT(*) FROM onboarding_plans
            WHERE request_id = %s
            """,
            (unknown_id,),
        ).fetchone()[0]

    assert count == 0


def test_concurrent_generation_creates_one_plan(client, request_id):
    barrier = Barrier(2)

    def generate():
        with TestClient(app) as separate_client:
            barrier.wait(timeout=10)
            return separate_client.post(
                f"/onboarding-requests/{request_id}/plan"
            )

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(generate) for _ in range(2)]
        responses = [future.result(timeout=30) for future in futures]

    assert sorted(r.status_code for r in responses) == [200, 201], [
        (r.status_code, r.text) for r in responses
    ]

    assert responses[0].json()["id"] == responses[1].json()["id"]

    with get_connection() as connection:
        count = connection.execute(
            """
            SELECT COUNT(*) FROM onboarding_plans
            WHERE request_id = %s
            """,
            (request_id,),
        ).fetchone()[0]

    assert count == 1