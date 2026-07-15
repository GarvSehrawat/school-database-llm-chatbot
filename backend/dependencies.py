"""FastAPI dependency providers for repositories and services."""

from fastapi import Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.llm.formatter import QueryAnswerFormatter
from backend.llm.hybrid_parser import HybridQueryParser
from backend.llm.query_service import QueryService
from backend.repositories.analytics_repository import AnalyticsRepository
from backend.repositories.attendance_repository import AttendanceRepository
from backend.repositories.fee_repository import FeeRepository
from backend.repositories.mark_repository import MarkRepository
from backend.repositories.student_repository import StudentRepository
from backend.services.analytics_service import AnalyticsService
from backend.services.attendance_service import AttendanceService
from backend.services.csv_service import CSVService
from backend.services.fee_service import FeeService
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


def get_attendance_repository(
    db: Session = Depends(get_db),
) -> AttendanceRepository:
    """Provide an AttendanceRepository for the current request."""

    return AttendanceRepository(db)


def get_fee_repository(
    db: Session = Depends(get_db),
) -> FeeRepository:
    """Provide a FeeRepository for the current request."""

    return FeeRepository(db)


def get_analytics_repository(
    db: Session = Depends(get_db),
) -> AnalyticsRepository:
    """Provide an AnalyticsRepository for the current request."""

    return AnalyticsRepository(db)


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


def get_attendance_service(
    attendance_repository: AttendanceRepository = Depends(
        get_attendance_repository
    ),
    student_service: StudentService = Depends(get_student_service),
) -> AttendanceService:
    """Provide an AttendanceService."""

    return AttendanceService(
        attendance_repository=attendance_repository,
        student_service=student_service,
    )


def get_fee_service(
    fee_repository: FeeRepository = Depends(get_fee_repository),
    student_service: StudentService = Depends(get_student_service),
) -> FeeService:
    """Provide a FeeService."""

    return FeeService(
        fee_repository=fee_repository,
        student_service=student_service,
    )


def get_analytics_service(
    analytics_repository: AnalyticsRepository = Depends(
        get_analytics_repository
    ),
    student_service: StudentService = Depends(get_student_service),
) -> AnalyticsService:
    """Provide an AnalyticsService."""

    return AnalyticsService(
        analytics_repository=analytics_repository,
        student_service=student_service,
    )


def get_csv_service(
    db: Session = Depends(get_db),
) -> CSVService:
    """Provide a CSVService for the current request."""

    return CSVService(db)


def get_query_parser() -> HybridQueryParser:
    """Provide the hybrid natural-language query parser."""

    return HybridQueryParser()


def get_query_answer_formatter() -> QueryAnswerFormatter:
    """Provide the human-readable query answer formatter."""

    return QueryAnswerFormatter()


def get_query_service(
    student_service: StudentService = Depends(get_student_service),
    mark_service: MarkService = Depends(get_mark_service),
    attendance_service: AttendanceService = Depends(
        get_attendance_service
    ),
    fee_service: FeeService = Depends(get_fee_service),
    analytics_service: AnalyticsService = Depends(
        get_analytics_service
    ),
    parser: HybridQueryParser = Depends(get_query_parser),
    formatter: QueryAnswerFormatter = Depends(
        get_query_answer_formatter
    ),
) -> QueryService:
    """Provide the natural-language query service."""

    return QueryService(
        student_service=student_service,
        mark_service=mark_service,
        attendance_service=attendance_service,
        fee_service=fee_service,
        analytics_service=analytics_service,
        parser=parser,
        formatter=formatter,
    )