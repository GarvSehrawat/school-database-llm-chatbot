"""FastAPI routes for student operations."""

from fastapi import APIRouter, Depends, status

from backend.dependencies import get_mark_service, get_student_service
from backend.schemas.mark import MarkResponse
from backend.schemas.student import StudentResponse
from backend.services.mark_service import MarkService
from backend.services.student_service import StudentService
from backend.dependencies import (
    get_attendance_service,
    get_fee_service,
    get_mark_service,
    get_student_service,
)
from backend.schemas.attendance import AttendanceResponse
from backend.services.attendance_service import AttendanceService
from backend.schemas.fee import FeeResponse
from backend.services.fee_service import FeeService


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
    "/{student_id}/attendance",
    response_model=list[AttendanceResponse],
    status_code=status.HTTP_200_OK,
)
def get_student_attendance(
    student_id: str,
    semester: int | None = None,
    service: AttendanceService = Depends(get_attendance_service),
) -> list[AttendanceResponse]:
    """Return a student's attendance, optionally filtered by semester."""

    return service.get_student_attendance(
        student_id=student_id,
        semester=semester,
    )



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
    "/{student_id}/fees",
    response_model=list[FeeResponse],
    status_code=status.HTTP_200_OK,
)
def get_student_fees(
    student_id: str,
    semester: int | None = None,
    service: FeeService = Depends(get_fee_service),
) -> list[FeeResponse]:
    """Return a student's fee records, optionally filtered by semester."""

    return service.get_student_fees(
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