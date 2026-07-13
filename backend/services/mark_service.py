"""Business logic for student marks."""

from backend.repositories.mark_repository import MarkRepository
from backend.schemas.mark import MarkResponse
from backend.services.student_service import StudentService


class MarkService:
    """Handles mark-related business logic."""

    def __init__(
        self,
        mark_repository: MarkRepository,
        student_service: StudentService,
    ) -> None:
        self.mark_repository = mark_repository
        self.student_service = student_service

    def get_student_marks(
        self,
        student_id: str,
        semester: int | None = None,
    ) -> list[MarkResponse]:
        """
        Return a student's marks, optionally filtered by semester.

        The student is validated first so a missing student produces
        a proper 404 response later in the API layer.
        """
        normalized_id = student_id.strip().upper()

        self.student_service.get_student(normalized_id)

        rows = self.mark_repository.get_student_marks(
            student_id=normalized_id,
            semester=semester,
        )

        return [
            MarkResponse(
                subject_code=subject.subject_code,
                subject_name=subject.subject_name,
                semester=mark.semester,
                internal_marks=mark.internal_marks,
                external_marks=mark.external_marks,
                total_marks=mark.total_marks,
                grade=mark.grade,
                grade_point=mark.grade_point,
                exam_type=mark.exam_type,
                academic_year=mark.academic_year,
            )
            for mark, subject in rows
        ]