"""Business logic for student operations."""

from backend.models.student import Student
from backend.repositories.student_repository import StudentRepository
from backend.utils.exceptions import StudentNotFoundError


class StudentService:
    """Handles student-related business logic."""

    def __init__(self, repository: StudentRepository):
        self.repository = repository

    def get_student(self, student_id: str) -> Student:
        """
        Return a student by school ID.

        Raises:
            StudentNotFoundError: If no matching student exists.
        """
        normalized_id = student_id.strip().upper()

        student = self.repository.get_by_student_id(normalized_id)

        if student is None:
            raise StudentNotFoundError(normalized_id)

        return student

    def list_students(self) -> list[Student]:
        """Return all students."""

        return self.repository.get_all()