from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from app.schemas import OnboardingRequestCreate
from app.workflow import onboarding_graph


router = APIRouter(
    prefix="/plans",
    tags=["Planning"],
)


class DraftTaskResponse(BaseModel):
    title: str
    owner_team: str
    due_date: str


class PlanPreviewResponse(BaseModel):
    status: Literal["draft"]
    tasks: list[DraftTaskResponse]


@router.post("/preview", response_model=PlanPreviewResponse)
def preview_plan(payload: OnboardingRequestCreate):
    result = onboarding_graph.invoke(
        {"request": payload.model_dump(mode="json")}
    )

    return {
        "status": result["status"],
        "tasks": result["tasks"],
    }