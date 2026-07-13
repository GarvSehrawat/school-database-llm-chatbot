"""Repository for attendance-related database operations."""

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from backend.models.attendance import Attendance
from backend.models.student import Student
from backend.models.subject import Subject


class AttendanceRepository:
    """Handles database operations related to attendance."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_student_attendance(
        self,
        student_id: str,
        semester: int | None = None,
    ) -> list[tuple[Attendance, Subject | None]]:
        """
        Return attendance records with optional subject details.

        Args:
            student_id: School identifier such as STU101.
            semester: Optional semester filter.
        """

        statement: Select[tuple[Attendance, Subject | None]] = (
            select(Attendance, Subject)
            .join(Student, Attendance.student_id == Student.id)
            .outerjoin(Subject, Attendance.subject_id == Subject.id)
            .where(Student.student_id == student_id)
            .order_by(Attendance.semester, Subject.subject_code)
        )

        if semester is not None:
            statement = statement.where(Attendance.semester == semester)

        rows = self.db.execute(statement).all()

        return [(row.Attendance, row.Subject) for row in rows]