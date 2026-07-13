"""Pydantic schemas for student marks."""

from pydantic import BaseModel, ConfigDict


class MarkResponse(BaseModel):
    """Marks returned by the API."""

    subject_code: str
    subject_name: str

    semester: int

    internal_marks: float
    external_marks: float
    total_marks: float

    grade: str | None
    grade_point: float | None

    exam_type: str
    academic_year: str

    model_config = ConfigDict(from_attributes=True)