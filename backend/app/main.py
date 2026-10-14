import logging

import psycopg
from fastapi import FastAPI, HTTPException
from app.onboarding import router as onboarding_router
from app.database import get_connection
from app.planning import router as planning_router


logger = logging.getLogger("uvicorn.error")

app = FastAPI(
    title="OnboardOps API",
    description="AI-assisted employee onboarding",
    version="0.1.0",
)


app.include_router(onboarding_router)
app.include_router(planning_router)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "onboardops-api"}


@app.get("/ready")
def readiness_check():
    try:
        with get_connection() as connection:
            connection.execute("SELECT 1").fetchone()
    except psycopg.Error as exc:
        logger.warning(
            "Database readiness check failed: %s",
            type(exc).__name__,
        )
        raise HTTPException(
            status_code=503,
            detail="Database unavailable",
        ) from exc

    return {"status": "ready", "database": "connected"}