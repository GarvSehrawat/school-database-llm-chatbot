"""Pydantic schemas for analytics responses."""

from pydantic import BaseModel, Field


class TopStudentResponse(BaseModel):
    """Ranked student performance summary."""

    rank: int = Field(ge=1)
    student_id: str
    student_name: str
    branch: str
    semester: int
    average_marks: float