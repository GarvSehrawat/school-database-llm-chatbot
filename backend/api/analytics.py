"""FastAPI routes for analytics."""

from fastapi import APIRouter, Depends, Query, status

from backend.dependencies import get_analytics_service
from backend.schemas.analytics import TopStudentResponse
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
    """
    Return the highest-performing students.
    """

    return service.get_top_students(
        semester=semester,
        limit=limit,
    )