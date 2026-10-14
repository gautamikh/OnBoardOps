import pytest
from pydantic import ValidationError

from app.workflow import onboarding_graph


def make_request(name="Maya Example"):
    return {
        "employee_name": name,
        "job_title": "Backend Engineer",
        "department": "Engineering",
        "location": "Berlin",
        "start_date": "2026-11-02",
    }


def test_plan_assigns_owners_and_dates():
    result = onboarding_graph.invoke({"request": make_request()})

    assert result["status"] == "draft"

    dates_by_owner = {
        task["owner_team"]: task["due_date"]
        for task in result["tasks"]
    }

    assert dates_by_owner == {
        "HR": "2026-10-30",
        "IT": "2026-10-31",
        "Hiring Manager": "2026-11-02",
    }


def test_invalid_input_cannot_generate_plan():
    with pytest.raises(ValidationError):
        onboarding_graph.invoke({"request": make_request("   ")})


def test_separate_runs_do_not_share_employee_details():
    onboarding_graph.invoke({"request": make_request("Maya Example")})
    result = onboarding_graph.invoke({"request": make_request("Alex Example")})

    assert len(result["tasks"]) == 3
    assert all("Alex Example" in task["title"] for task in result["tasks"])
    assert all("Maya Example" not in task["title"] for task in result["tasks"])