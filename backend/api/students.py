"""FastAPI routes for student operations."""

from fastapi import APIRouter, Depends, status

from backend.dependencies import get_mark_service, get_student_service
from backend.schemas.mark import MarkResponse
from backend.schemas.student import StudentResponse
from backend.services.mark_service import MarkService
from backend.services.student_service import StudentService


router = APIRouter(
    prefix="/api/v1/students",
    tags=["Students"],
)


@router.get(
    "",
    response_model=list[StudentResponse],
    status_code=status.HTTP_200_OK,
)
def list_students(
    service: StudentService = Depends(get_student_service),
) -> list[StudentResponse]:
    """Return all students."""

    students = service.list_students()

    return [
        StudentResponse.model_validate(student)
        for student in students
    ]


@router.get(
    "/{student_id}/marks",
    response_model=list[MarkResponse],
    status_code=status.HTTP_200_OK,
)
def get_student_marks(
    student_id: str,
    semester: int | None = None,
    service: MarkService = Depends(get_mark_service),
) -> list[MarkResponse]:
    """Return a student's marks, optionally filtered by semester."""

    return service.get_student_marks(
        student_id=student_id,
        semester=semester,
    )


@router.get(
    "/{student_id}",
    response_model=StudentResponse,
    status_code=status.HTTP_200_OK,
)
def get_student(
    student_id: str,
    service: StudentService = Depends(get_student_service),
) -> StudentResponse:
    """Return one student using the school student ID."""

    student = service.get_student(student_id)

    return StudentResponse.model_validate(student)