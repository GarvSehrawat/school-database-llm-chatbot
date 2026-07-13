"""FastAPI routes for school analytics."""

from fastapi import APIRouter, Depends, Query, status

from backend.dependencies import get_analytics_service
from backend.schemas.analytics import (
    BranchTopperResponse,
    LowAttendanceResponse,
    PendingFeeResponse,
    StudentRankResponse,
    TopStudentResponse,
)
from backend.services.analytics_service import AnalyticsService


router = APIRouter(
    prefix="/api/v1/analytics",
    tags=["Analytics"],
)


@router.get(
    "/top-students",
    response_model=list[TopStudentResponse],
    status_code=status.HTTP_200_OK,
)
def get_top_students(
    semester: int = Query(..., ge=1, le=8),
    limit: int = Query(5, ge=1, le=100),
    service: AnalyticsService = Depends(get_analytics_service),
) -> list[TopStudentResponse]:
    """Return the highest-performing students for a semester."""

    return service.get_top_students(
        semester=semester,
        limit=limit,
    )


@router.get(
    "/low-attendance",
    response_model=list[LowAttendanceResponse],
    status_code=status.HTTP_200_OK,
)
def get_low_attendance_students(
    threshold: float = Query(75.0, ge=0, le=100),
    semester: int | None = Query(None, ge=1, le=8),
    service: AnalyticsService = Depends(get_analytics_service),
) -> list[LowAttendanceResponse]:
    """Return students whose average attendance is below the threshold."""

    return service.get_low_attendance_students(
        threshold=threshold,
        semester=semester,
    )


@router.get(
    "/pending-fees",
    response_model=list[PendingFeeResponse],
    status_code=status.HTTP_200_OK,
)
def get_pending_fee_students(
    semester: int | None = Query(None, ge=1, le=8),
    service: AnalyticsService = Depends(get_analytics_service),
) -> list[PendingFeeResponse]:
    """Return students with pending, partial, or overdue fees."""

    return service.get_pending_fee_students(
        semester=semester,
    )


@router.get(
    "/student-rank/{student_id}",
    response_model=StudentRankResponse,
    status_code=status.HTTP_200_OK,
)
def get_student_rank(
    student_id: str,
    semester: int = Query(..., ge=1, le=8),
    service: AnalyticsService = Depends(get_analytics_service),
) -> StudentRankResponse:
    """Return a student's academic rank for a semester."""

    return service.get_student_rank(
        student_id=student_id,
        semester=semester,
    )


@router.get(
    "/branch-toppers",
    response_model=list[BranchTopperResponse],
    status_code=status.HTTP_200_OK,
)
def get_branch_toppers(
    semester: int = Query(..., ge=1, le=8),
    service: AnalyticsService = Depends(get_analytics_service),
) -> list[BranchTopperResponse]:
    """Return the highest-performing student from each branch."""

    return service.get_branch_toppers(
        semester=semester,
    )