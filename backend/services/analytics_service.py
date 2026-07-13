"""Business logic for academic analytics."""

from backend.repositories.analytics_repository import AnalyticsRepository
from backend.schemas.analytics import TopStudentResponse


class AnalyticsService:
    """Handles analytics-related business logic."""

    def __init__(
        self,
        analytics_repository: AnalyticsRepository,
    ) -> None:
        self.analytics_repository = analytics_repository

    def get_top_students(
        self,
        semester: int,
        limit: int = 5,
    ) -> list[TopStudentResponse]:
        """
        Return the highest-performing students for a semester.

        Args:
            semester: Semester number between 1 and 8.
            limit: Maximum number of students to return.
        """

        if semester < 1 or semester > 8:
            raise ValueError("Semester must be between 1 and 8.")

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