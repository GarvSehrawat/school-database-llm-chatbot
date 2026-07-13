"""Business logic for student fee records."""

from backend.repositories.fee_repository import FeeRepository
from backend.schemas.fee import FeeResponse
from backend.services.student_service import StudentService


class FeeService:
    """Handles fee-related business logic."""

    def __init__(
        self,
        fee_repository: FeeRepository,
        student_service: StudentService,
    ) -> None:
        self.fee_repository = fee_repository
        self.student_service = student_service

    def get_student_fees(
        self,
        student_id: str,
        semester: int | None = None,
    ) -> list[FeeResponse]:
        """Return a student's fee records, optionally filtered by semester."""

        normalized_id = student_id.strip().upper()

        # Validate that the student exists first.
        self.student_service.get_student(normalized_id)

        fee_records = self.fee_repository.get_student_fees(
            student_id=normalized_id,
            semester=semester,
        )

        return [
            FeeResponse.model_validate(fee)
            for fee in fee_records
        ]