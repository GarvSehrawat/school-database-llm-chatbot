"""FastAPI dependency providers for repositories and services."""

from fastapi import Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.repositories.mark_repository import MarkRepository
from backend.repositories.student_repository import StudentRepository
from backend.services.mark_service import MarkService
from backend.services.student_service import StudentService


def get_student_repository(
    db: Session = Depends(get_db),
) -> StudentRepository:
    """Provide a StudentRepository for the current request."""
    return StudentRepository(db)


def get_mark_repository(
    db: Session = Depends(get_db),
) -> MarkRepository:
    """Provide a MarkRepository for the current request."""
    return MarkRepository(db)


def get_student_service(
    repository: StudentRepository = Depends(get_student_repository),
) -> StudentService:
    """Provide a StudentService."""
    return StudentService(repository)


def get_mark_service(
    mark_repository: MarkRepository = Depends(get_mark_repository),
    student_service: StudentService = Depends(get_student_service),
) -> MarkService:
    """Provide a MarkService."""
    return MarkService(
        mark_repository=mark_repository,
        student_service=student_service,
    )