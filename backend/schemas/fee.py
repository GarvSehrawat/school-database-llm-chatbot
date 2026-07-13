"""Pydantic schemas for student fee records."""

from datetime import date

from pydantic import BaseModel, ConfigDict

from backend.models.fee import FeeStatus


class FeeResponse(BaseModel):
    """Fee record returned by the API."""

    semester: int
    total_fee: int
    amount_paid: int
    amount_due: int
    status: FeeStatus
    due_date: date | None
    payment_date: date | None
    academic_year: str

    model_config = ConfigDict(from_attributes=True)