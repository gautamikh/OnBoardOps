import logging
from uuid import UUID, uuid4

import psycopg
from fastapi import APIRouter, HTTPException
from psycopg.rows import dict_row

from app.database import get_connection
from app.schemas import OnboardingRequestCreate, OnboardingRequestRead


logger = logging.getLogger("uvicorn.error")

router = APIRouter(
    prefix="/onboarding-requests",
    tags=["Onboarding"],
)


@router.post("", response_model=OnboardingRequestRead, status_code=201)
def create_request(payload: OnboardingRequestCreate):
    request_id = uuid4()

    try:
        with get_connection() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    INSERT INTO onboarding_requests (
                        id, employee_name, job_title,
                        department, location, start_date
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING *
                    """,
                    (
                        request_id,
                        payload.employee_name,
                        payload.job_title,
                        payload.department,
                        payload.location,
                        payload.start_date,
                    ),
                )
                row = cursor.fetchone()
    except psycopg.OperationalError as exc:
        logger.warning("Create request failed: %s", type(exc).__name__)
        raise HTTPException(
            status_code=503,
            detail="Database unavailable",
        ) from exc

    return row


@router.get("/{request_id}", response_model=OnboardingRequestRead)
def get_request(request_id: UUID):
    try:
        with get_connection() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    "SELECT * FROM onboarding_requests WHERE id = %s",
                    (request_id,),
                )
                row = cursor.fetchone()
    except psycopg.OperationalError as exc:
        logger.warning("Read request failed: %s", type(exc).__name__)
        raise HTTPException(
            status_code=503,
            detail="Database unavailable",
        ) from exc

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Onboarding request not found",
        )

    return row