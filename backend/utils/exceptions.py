"""Custom application exceptions."""


class ApplicationError(Exception):
    """Base class for expected application errors."""

    error_code = "APPLICATION_ERROR"


class StudentNotFoundError(ApplicationError):
    """Raised when a student cannot be found."""

    error_code = "STUDENT_NOT_FOUND"

    def __init__(self, student_id: str) -> None:
        self.student_id = student_id
        super().__init__(f"Student with ID '{student_id}' was not found.")