"""Repository for marks-related database operations."""

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from backend.models.mark import Mark
from backend.models.student import Student
from backend.models.subject import Subject


class MarkRepository:
    """Handles database operations related to student marks."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_student_marks(
        self,
        student_id: str,
        semester: int | None = None,
    ) -> list[tuple[Mark, Subject]]:
        """
        Return a student's marks together with subject information.

        Args:
            student_id: School identifier such as STU101.
            semester: Optional semester filter.
        """

        statement: Select[tuple[Mark, Subject]] = (
            select(Mark, Subject)
            .join(Student, Mark.student_id == Student.id)
            .join(Subject, Mark.subject_id == Subject.id)
            .where(Student.student_id == student_id)
            .order_by(Mark.semester, Subject.subject_code)
        )

        if semester is not None:
            statement = statement.where(Mark.semester == semester)

        rows = self.db.execute(statement).all()

        return [(row.Mark, row.Subject) for row in rows]