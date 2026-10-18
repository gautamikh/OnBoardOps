from langgraph.graph import END, START, StateGraph

from app.mcp_client import lookup_employee
from app.workflow import OnboardingState, draft_tasks, validate_details


class EmployeePlanState(OnboardingState, total=False):
    employee_id: str
    job_title: str
    start_date: str


async def fetch_employee(state: EmployeePlanState) -> dict:
    employee = await lookup_employee(state["employee_id"])

    return {
        "request": {
            "employee_name": employee.name,
            "job_title": state["job_title"],
            "department": employee.department,
            "location": employee.location,
            "start_date": state["start_date"],
        }
    }


builder = StateGraph(EmployeePlanState)

builder.add_node("fetch_employee", fetch_employee)
builder.add_node("validate_details", validate_details)
builder.add_node("draft_tasks", draft_tasks)

builder.add_edge(START, "fetch_employee")
builder.add_edge("fetch_employee", "validate_details")
builder.add_edge("validate_details", "draft_tasks")
builder.add_edge("draft_tasks", END)

employee_plan_graph = builder.compile()