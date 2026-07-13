"""Pydantic schemas for student API responses."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class StudentBase(BaseModel):
    """Common student fields."""

    student_id: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr | None = None
    branch: str = Field(min_length=1, max_length=30)
    current_semester: int = Field(ge=1, le=8)
    section: str | None = None
    admission_year: int


class StudentResponse(StudentBase):
    """Student data returned by the API."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)