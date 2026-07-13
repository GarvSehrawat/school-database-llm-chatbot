"""Repository for fee-related database operations."""

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from backend.models.fee import Fee
from backend.models.student import Student


class FeeRepository:
    """Handles database operations related to student fees."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_student_fees(
        self,
        student_id: str,
        semester: int | None = None,
    ) -> list[Fee]:
        """
        Return a student's fee records.

        Args:
            student_id: School identifier such as STU101.
            semester: Optional semester filter.
        """

        statement: Select[tuple[Fee]] = (
            select(Fee)
            .join(Student, Fee.student_id == Student.id)
            .where(Student.student_id == student_id)
            .order_by(Fee.semester, Fee.academic_year)
        )

        if semester is not None:
            statement = statement.where(Fee.semester == semester)

        return list(self.db.scalars(statement))