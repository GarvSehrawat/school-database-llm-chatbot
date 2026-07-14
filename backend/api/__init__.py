"""API router exports."""

from backend.api.analytics import router as analytics_router
from backend.api.students import router as students_router
from backend.api.uploads import router as uploads_router

__all__ = [
    "analytics_router",
    "students_router",
    "uploads_router",
]