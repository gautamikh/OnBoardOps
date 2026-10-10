from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OnboardingRequestCreate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    employee_name: str = Field(min_length=1, max_length=120)
    job_title: str = Field(min_length=1, max_length=120)
    department: str = Field(min_length=1, max_length=80)
    location: str = Field(min_length=1, max_length=80)
    start_date: date


class OnboardingRequestRead(OnboardingRequestCreate):
    id: UUID
    status: str
    created_at: datetime