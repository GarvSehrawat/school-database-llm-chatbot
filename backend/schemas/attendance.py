"""Pydantic schemas for student attendance."""

from pydantic import BaseModel, ConfigDict


class AttendanceResponse(BaseModel):
    """Attendance record returned by the API."""

    subject_code: str | None
    subject_name: str | None

    semester: int
    classes_held: int
    classes_attended: int
    attendance_percentage: float
    academic_year: str

    model_config = ConfigDict(from_attributes=True)