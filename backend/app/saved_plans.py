import logging
from datetime import date, datetime
from typing import Literal
from uuid import UUID, uuid4

import psycopg
from fastapi import APIRouter, HTTPException, Response
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from pydantic import BaseModel

from app.database import get_connection
from app.workflow import onboarding_graph


logger = logging.getLogger("uvicorn.error")

router = APIRouter(
    prefix="/onboarding-requests",
    tags=["Saved plans"],
)


class SavedTask(BaseModel):
    title: str
    owner_team: str
    due_date: date


class SavedPlan(BaseModel):
    id: UUID
    request_id: UUID
    status: Literal["draft", "approved", "rejected"]
    tasks: list[SavedTask]
    created_at: datetime


@router.post("/{request_id}/plan", response_model=SavedPlan)
def generate_saved_plan(request_id: UUID, response: Response):
    created = False

    try:
        with get_connection() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT employee_name, job_title, department,
                           location, start_date
                    FROM onboarding_requests
                    WHERE id = %s
                    """,
                    (request_id,),
                )
                request = cursor.fetchone()

                if request is None:
                    raise HTTPException(
                        status_code=404,
                        detail="Onboarding request not found",
                    )

                cursor.execute(
                    """
                    SELECT * FROM onboarding_plans
                    WHERE request_id = %s
                    """,
                    (request_id,),
                )
                plan = cursor.fetchone()

                if plan is None:
                    result = onboarding_graph.invoke({"request": request})

                    cursor.execute(
                        """
                        INSERT INTO onboarding_plans (
                            id, request_id, tasks
                        )
                        VALUES (%s, %s, %s)
                        ON CONFLICT (request_id) DO NOTHING
                        RETURNING *
                        """,
                        (
                            uuid4(),
                            request_id,
                            Jsonb(result["tasks"]),
                        ),
                    )
                    plan = cursor.fetchone()
                    created = plan is not None

                    # Another request may have saved the plan first.
                    if plan is None:
                        cursor.execute(
                            """
                            SELECT * FROM onboarding_plans
                            WHERE request_id = %s
                            """,
                            (request_id,),
                        )
                        plan = cursor.fetchone()

    except psycopg.OperationalError as exc:
        logger.warning("Save plan failed: %s", type(exc).__name__)
        raise HTTPException(
            status_code=503,
            detail="Database unavailable",
        ) from exc

    response.status_code = 201 if created else 200
    return plan


@router.get("/{request_id}/plan", response_model=SavedPlan)
def get_saved_plan(request_id: UUID):
    try:
        with get_connection() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT * FROM onboarding_plans
                    WHERE request_id = %s
                    """,
                    (request_id,),
                )
                plan = cursor.fetchone()

    except psycopg.OperationalError as exc:
        logger.warning("Read plan failed: %s", type(exc).__name__)
        raise HTTPException(
            status_code=503,
            detail="Database unavailable",
        ) from exc

    if plan is None:
        raise HTTPException(
            status_code=404,
            detail="Saved plan not found",
        )

    return plan