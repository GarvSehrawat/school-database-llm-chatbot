"""Repository for analytics-related database queries."""

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from backend.models.mark import Mark
from backend.models.student import Student


class AnalyticsRepository:
    """Handles aggregate database queries for academic analytics."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_top_students(
        self,
        semester: int,
        limit: int = 5,
    ) -> list[tuple[Student, float]]:
        """
        Return the top students for a semester by average marks.

        Students are ordered from highest to lowest average score.
        """

        average_marks = func.avg(Mark.total_marks).label("average_marks")

        statement: Select[tuple[Student, float]] = (
            select(Student, average_marks)
            .join(Mark, Mark.student_id == Student.id)
            .where(Mark.semester == semester)
            .group_by(Student.id)
            .order_by(average_marks.desc(), Student.student_id.asc())
            .limit(limit)
        )

        rows = self.db.execute(statement).all()

        return [
            (row.Student, float(row.average_marks))
            for row in rows
        ]