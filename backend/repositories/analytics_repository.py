"""Repository for analytics-related database queries."""

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from backend.models.attendance import Attendance
from backend.models.fee import Fee, FeeStatus
from backend.models.mark import Mark
from backend.models.student import Student


class AnalyticsRepository:
    """Handles aggregate database queries for school analytics."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_top_students(
        self,
        semester: int,
        limit: int = 5,
    ) -> list[tuple[Student, float]]:
        """Return the top students for a semester by average marks."""

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

    def get_low_attendance_students(
        self,
        threshold: float = 75.0,
        semester: int | None = None,
    ) -> list[tuple[Student, float]]:
        """Return students whose average attendance is below a threshold."""

        average_attendance = func.avg(
            Attendance.attendance_percentage
        ).label("average_attendance")

        statement: Select[tuple[Student, float]] = (
            select(Student, average_attendance)
            .join(
                Attendance,
                Attendance.student_id == Student.id,
            )
            .group_by(Student.id)
            .having(average_attendance < threshold)
            .order_by(
                average_attendance.asc(),
                Student.student_id.asc(),
            )
        )

        if semester is not None:
            statement = statement.where(
                Attendance.semester == semester
            )

        rows = self.db.execute(statement).all()

        return [
            (row.Student, float(row.average_attendance))
            for row in rows
        ]

    def get_pending_fee_students(
        self,
        semester: int | None = None,
    ) -> list[tuple[Student, Fee]]:
        """Return students with pending, partial, or overdue fee records."""

        unpaid_statuses = [
            FeeStatus.PENDING,
            FeeStatus.PARTIALLY_PAID,
            FeeStatus.OVERDUE,
        ]

        statement: Select[tuple[Student, Fee]] = (
            select(Student, Fee)
            .join(Fee, Fee.student_id == Student.id)
            .where(
                Fee.status.in_(unpaid_statuses),
                Fee.amount_due > 0,
            )
            .order_by(
                Fee.amount_due.desc(),
                Student.student_id.asc(),
            )
        )

        if semester is not None:
            statement = statement.where(Fee.semester == semester)

        rows = self.db.execute(statement).all()

        return [
            (row.Student, row.Fee)
            for row in rows
        ]

    def get_student_rank(
        self,
        student_id: str,
        semester: int,
    ) -> tuple[int, Student, float] | None:
        """Return a student's dense rank by average marks."""

        average_marks = func.avg(Mark.total_marks).label("average_marks")

        ranked_students_subquery = (
            select(
                Student.id.label("student_pk"),
                Student.student_id.label("student_id"),
                Student.name.label("student_name"),
                average_marks,
            )
            .join(Mark, Mark.student_id == Student.id)
            .where(Mark.semester == semester)
            .group_by(Student.id)
            .subquery()
        )

        dense_rank = func.dense_rank().over(
            order_by=ranked_students_subquery.c.average_marks.desc()
        ).label("rank")

        ranked_statement = select(
            ranked_students_subquery.c.student_pk,
            ranked_students_subquery.c.student_id,
            ranked_students_subquery.c.student_name,
            ranked_students_subquery.c.average_marks,
            dense_rank,
        ).subquery()

        statement = (
            select(
                Student,
                ranked_statement.c.average_marks,
                ranked_statement.c.rank,
            )
            .join(
                ranked_statement,
                ranked_statement.c.student_pk == Student.id,
            )
            .where(
                ranked_statement.c.student_id == student_id
            )
        )

        row = self.db.execute(statement).first()

        if row is None:
            return None

        return (
            int(row.rank),
            row.Student,
            float(row.average_marks),
        )

    def get_branch_toppers(
        self,
        semester: int,
    ) -> list[tuple[str, Student, float]]:
        """Return the highest-performing student from each branch."""

        average_marks = func.avg(Mark.total_marks).label("average_marks")

        student_averages = (
            select(
                Student.id.label("student_pk"),
                Student.branch.label("branch"),
                average_marks,
            )
            .join(Mark, Mark.student_id == Student.id)
            .where(Mark.semester == semester)
            .group_by(Student.id, Student.branch)
            .subquery()
        )

        branch_rank = func.dense_rank().over(
            partition_by=student_averages.c.branch,
            order_by=student_averages.c.average_marks.desc(),
        ).label("branch_rank")

        ranked_students = (
            select(
                student_averages.c.student_pk,
                student_averages.c.branch,
                student_averages.c.average_marks,
                branch_rank,
            )
            .subquery()
        )

        statement = (
            select(
                ranked_students.c.branch,
                Student,
                ranked_students.c.average_marks,
            )
            .join(
                Student,
                Student.id == ranked_students.c.student_pk,
            )
            .where(ranked_students.c.branch_rank == 1)
            .order_by(
                ranked_students.c.branch.asc(),
                Student.student_id.asc(),
            )
        )

        rows = self.db.execute(statement).all()

        return [
            (
                str(row.branch),
                row.Student,
                float(row.average_marks),
            )
            for row in rows
        ]