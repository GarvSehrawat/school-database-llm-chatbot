"""Business logic for school analytics."""

from backend.repositories.analytics_repository import AnalyticsRepository
from backend.schemas.analytics import (
    BranchTopperResponse,
    LowAttendanceResponse,
    PendingFeeResponse,
    StudentRankResponse,
    TopStudentResponse,
)
from backend.services.student_service import StudentService


class AnalyticsService:
    """Handles analytics-related business logic."""

    def __init__(
        self,
        analytics_repository: AnalyticsRepository,
        student_service: StudentService,
    ) -> None:
        self.analytics_repository = analytics_repository
        self.student_service = student_service

    @staticmethod
    def _validate_semester(semester: int) -> None:
        """Ensure a semester is between 1 and 8."""

        if semester < 1 or semester > 8:
            raise ValueError("Semester must be between 1 and 8.")

    def get_top_students(
        self,
        semester: int,
        limit: int = 5,
    ) -> list[TopStudentResponse]:
        """Return the highest-performing students for a semester."""

        self._validate_semester(semester)

        if limit < 1 or limit > 100:
            raise ValueError("Limit must be between 1 and 100.")

        rows = self.analytics_repository.get_top_students(
            semester=semester,
            limit=limit,
        )

        return [
            TopStudentResponse(
                rank=index,
                student_id=student.student_id,
                student_name=student.name,
                branch=student.branch,
                semester=semester,
                average_marks=round(average_marks, 2),
            )
            for index, (student, average_marks) in enumerate(
                rows,
                start=1,
            )
        ]

    def get_low_attendance_students(
        self,
        threshold: float = 75.0,
        semester: int | None = None,
    ) -> list[LowAttendanceResponse]:
        """Return students whose average attendance is below a threshold."""

        if threshold < 0 or threshold > 100:
            raise ValueError("Attendance threshold must be between 0 and 100.")

        if semester is not None:
            self._validate_semester(semester)

        rows = self.analytics_repository.get_low_attendance_students(
            threshold=threshold,
            semester=semester,
        )

        return [
            LowAttendanceResponse(
                student_id=student.student_id,
                student_name=student.name,
                branch=student.branch,
                attendance_percentage=round(average_attendance, 2),
            )
            for student, average_attendance in rows
        ]

    def get_pending_fee_students(
        self,
        semester: int | None = None,
    ) -> list[PendingFeeResponse]:
        """Return students who still have outstanding fee amounts."""

        if semester is not None:
            self._validate_semester(semester)

        rows = self.analytics_repository.get_pending_fee_students(
            semester=semester,
        )

        return [
            PendingFeeResponse(
                student_id=student.student_id,
                student_name=student.name,
                amount_due=fee.amount_due,
                semester=fee.semester,
            )
            for student, fee in rows
        ]

    def get_student_rank(
        self,
        student_id: str,
        semester: int,
    ) -> StudentRankResponse:
        """Return a student's dense rank for a semester."""

        self._validate_semester(semester)

        normalized_id = student_id.strip().upper()

        # Ensures a missing student gets the existing custom 404 response.
        self.student_service.get_student(normalized_id)

        result = self.analytics_repository.get_student_rank(
            student_id=normalized_id,
            semester=semester,
        )

        if result is None:
            raise ValueError(
                f"No marks were found for student '{normalized_id}' "
                f"in semester {semester}."
            )

        rank, student, average_marks = result

        return StudentRankResponse(
            rank=rank,
            student_id=student.student_id,
            student_name=student.name,
            average_marks=round(average_marks, 2),
        )

    def get_branch_toppers(
        self,
        semester: int,
    ) -> list[BranchTopperResponse]:
        """Return the highest-performing student from each branch."""

        self._validate_semester(semester)

        rows = self.analytics_repository.get_branch_toppers(
            semester=semester,
        )

        return [
            BranchTopperResponse(
                branch=branch,
                student_id=student.student_id,
                student_name=student.name,
                average_marks=round(average_marks, 2),
            )
            for branch, student, average_marks in rows
        ]