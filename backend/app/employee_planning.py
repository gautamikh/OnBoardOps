from datetime import date
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.mcp_client import EmployeeNotFound, MCPUnavailable
from app.mcp_workflow import employee_plan_graph
from app.planning import DraftTaskResponse
from app.schemas import OnboardingRequestCreate


router = APIRouter(
    prefix="/plans",
    tags=["Employee planning"],
)


class EmployeePlanInput(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    employee_id: str = Field(pattern=r"^EMP-\d{3}$")
    job_title: str = Field(min_length=1, max_length=120)
    start_date: date


class EmployeePlanResponse(BaseModel):
    employee_id: str
    request: OnboardingRequestCreate
    status: Literal["draft"]
    tasks: list[DraftTaskResponse]


@router.post("/from-employee", response_model=EmployeePlanResponse)
async def preview_employee_plan(payload: EmployeePlanInput):
    try:
        result = await employee_plan_graph.ainvoke(
            payload.model_dump(mode="json")
        )
    except EmployeeNotFound as exc:
        raise HTTPException(404, "Employee not found") from exc
    except MCPUnavailable as exc:
        raise HTTPException(
            503, "Employee directory temporarily unavailable"
        ) from exc

    return {
        "employee_id": payload.employee_id,
        "request": result["request"],
        "status": result["status"],
        "tasks": result["tasks"],
    }