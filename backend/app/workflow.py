from datetime import date, timedelta
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from app.schemas import OnboardingRequestCreate


class DraftTask(TypedDict):
    title: str
    owner_team: str
    due_date: str


class OnboardingState(TypedDict, total=False):
    request: dict
    tasks: list[DraftTask]
    status: str


def validate_details(state: OnboardingState) -> dict:
    request = OnboardingRequestCreate.model_validate(state["request"])

    return {
        "request": request.model_dump(mode="json"),
        "status": "validated",
    }


def draft_tasks(state: OnboardingState) -> dict:
    request = state["request"]
    start_date = date.fromisoformat(request["start_date"])
    employee_name = request["employee_name"]

    tasks: list[DraftTask] = [
        {
            "title": f"Prepare onboarding documents for {employee_name}",
            "owner_team": "HR",
            "due_date": (start_date - timedelta(days=3)).isoformat(),
        },
        {
            "title": f"Prepare equipment for {employee_name}",
            "owner_team": "IT",
            "due_date": (start_date - timedelta(days=2)).isoformat(),
        },
        {
            "title": f"Schedule welcome meeting for {employee_name}",
            "owner_team": "Hiring Manager",
            "due_date": start_date.isoformat(),
        },
    ]

    return {
        "tasks": tasks,
        "status": "draft",
    }


builder = StateGraph(OnboardingState)

builder.add_node("validate_details", validate_details)
builder.add_node("draft_tasks", draft_tasks)

builder.add_edge(START, "validate_details")
builder.add_edge("validate_details", "draft_tasks")
builder.add_edge("draft_tasks", END)

onboarding_graph = builder.compile()