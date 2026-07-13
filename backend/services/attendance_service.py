"""Business logic for student attendance."""

from backend.repositories.attendance_repository import AttendanceRepository
from backend.schemas.attendance import AttendanceResponse
from backend.services.student_service import StudentService


class AttendanceService:
    """Handles attendance-related business logic."""

    def __init__(
        self,
        attendance_repository: AttendanceRepository,
        student_service: StudentService,
    ) -> None:
        self.attendance_repository = attendance_repository
        self.student_service = student_service

    def get_student_attendance(
        self,
        student_id: str,
        semester: int | None = None,
    ) -> list[AttendanceResponse]:
        """
        Return a student's attendance records.
        """

        normalized_id = student_id.strip().upper()

        # Validate student exists
        self.student_service.get_student(normalized_id)

        rows = self.attendance_repository.get_student_attendance(
            student_id=normalized_id,
            semester=semester,
        )

        return [
            AttendanceResponse(
                subject_code=(
                    subject.subject_code
                    if subject is not None
                    else None
                ),
                subject_name=(
                    subject.subject_name
                    if subject is not None
                    else None
                ),
                semester=attendance.semester,
                classes_held=attendance.classes_held,
                classes_attended=attendance.classes_attended,
                attendance_percentage=attendance.attendance_percentage,
                academic_year=attendance.academic_year,
            )
            for attendance, subject in rows
        ]