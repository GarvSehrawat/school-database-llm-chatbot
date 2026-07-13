"""Pydantic schemas for analytics responses."""

from pydantic import BaseModel, Field


class TopStudentResponse(BaseModel):
    rank: int = Field(ge=1)
    student_id: str
    student_name: str
    branch: str
    semester: int
    average_marks: float


class LowAttendanceResponse(BaseModel):
    student_id: str
    student_name: str
    branch: str
    attendance_percentage: float


class PendingFeeResponse(BaseModel):
    student_id: str
    student_name: str
    amount_due: int
    semester: int


class StudentRankResponse(BaseModel):
    rank: int
    student_id: str
    student_name: str
    average_marks: float


class BranchTopperResponse(BaseModel):
    branch: str
    student_id: str
    student_name: str
    average_marks: float