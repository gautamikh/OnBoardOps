import logging
from typing import Literal
from uuid import UUID

import psycopg
from fastapi import APIRouter, HTTPException
from langgraph.types import Command
from psycopg.rows import dict_row
from pydantic import BaseModel, ConfigDict

from app.approval_workflow import build_review_graph
from app.checkpoints import get_checkpointer
from app.database import get_connection
from app.saved_plans import SavedPlan


logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/plans", tags=["Plan reviews"])


class DecisionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: Literal["approve", "reject"]


class ReviewResponse(BaseModel):
    plan: SavedPlan
    workflow_status: Literal[
        "awaiting_approval", "approved", "rejected"
    ]
    waiting_for_approval: bool


def process_review(plan_id: UUID, decision: str | None = None):
    conflict = False

    try:
        with get_connection() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                # Serialize review operations for this particular plan.
                cursor.execute(
                    """
                    SELECT * FROM onboarding_plans
                    WHERE id = %s
                    FOR UPDATE
                    """,
                    (plan_id,),
                )
                plan = cursor.fetchone()

                if plan is None:
                    raise HTTPException(404, "Plan not found")

                config = {
                    "configurable": {
                        "thread_id": f"plan-review:{plan_id}"
                    }
                }

                with get_checkpointer() as checkpointer:
                    graph = build_review_graph(checkpointer)
                    snapshot = graph.get_state(config)

                    # Recover execution interrupted between graph steps.
                    if snapshot.next and not snapshot.interrupts:
                        graph.invoke(None, config=config)
                        snapshot = graph.get_state(config)

                    if not snapshot.values:
                        if decision is not None:
                            raise HTTPException(
                                409, "Start the plan review first"
                            )

                        if plan["status"] != "draft":
                            raise HTTPException(
                                409, "Only draft plans can start a review"
                            )

                        graph.invoke(
                            {
                                "plan_id": str(plan_id),
                                "tasks": plan["tasks"],
                            },
                            config=config,
                        )
                        snapshot = graph.get_state(config)

                    # Approval must refer to the exact saved task list.
                    if (
                        snapshot.values["plan_id"] != str(plan_id)
                        or snapshot.values["tasks"] != plan["tasks"]
                    ):
                        raise HTTPException(
                            409, "Plan changed after review started"
                        )

                    workflow_status = snapshot.values["status"]

                    if decision is not None:
                        desired_status = (
                            "approved"
                            if decision == "approve"
                            else "rejected"
                        )

                        if workflow_status in ("approved", "rejected"):
                            conflict = workflow_status != desired_status
                        else:
                            if not snapshot.interrupts:
                                raise HTTPException(
                                    409, "Review is not awaiting a decision"
                                )

                            graph.invoke(
                                Command(resume=decision),
                                config=config,
                            )
                            snapshot = graph.get_state(config)
                            workflow_status = snapshot.values["status"]

                    # Reconcile the business record with the checkpoint.
                    # Retrying repairs an interrupted database update.
                    if workflow_status in ("approved", "rejected"):
                        cursor.execute(
                            """
                            UPDATE onboarding_plans
                            SET status = %s
                            WHERE id = %s
                            RETURNING *
                            """,
                            (workflow_status, plan_id),
                        )
                        plan = cursor.fetchone()

                    result = {
                        "plan": plan,
                        "workflow_status": workflow_status,
                        "waiting_for_approval": bool(snapshot.interrupts),
                    }

    except (
        psycopg.OperationalError,
        psycopg.errors.QueryCanceled,
    ) as exc:
        logger.warning("Review operation failed: %s", type(exc).__name__)
        raise HTTPException(
            503, "Review storage temporarily unavailable; retry the request"
        ) from exc

    # Raise after committing any recovery of the saved plan status.
    if conflict:
        raise HTTPException(
            409, "This plan already has a different final decision"
        )

    return result


@router.post("/{plan_id}/review", response_model=ReviewResponse)
def start_or_recover_review(plan_id: UUID):
    return process_review(plan_id)


@router.post("/{plan_id}/decision", response_model=ReviewResponse)
def submit_decision(plan_id: UUID, payload: DecisionInput):
    return process_review(plan_id, payload.decision)