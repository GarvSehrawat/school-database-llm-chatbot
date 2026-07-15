"""Safely route parsed natural-language queries to existing services."""

from __future__ import annotations

from fastapi.encoders import jsonable_encoder

from backend.llm.parser import QueryParser
from backend.llm.schemas import ParsedQuery, QueryIntent, QueryResult
from backend.services.analytics_service import AnalyticsService
from backend.services.attendance_service import AttendanceService
from backend.services.fee_service import FeeService
from backend.services.mark_service import MarkService
from backend.services.student_service import StudentService


class QueryService:
    """
    Execute natural-language school queries using predefined operations.

    This service never generates or executes arbitrary SQL. The parser selects
    a supported intent, and that intent is mapped to an existing service method.
    """

    def __init__(
        self,
        student_service: StudentService,
        mark_service: MarkService,
        attendance_service: AttendanceService,
        fee_service: FeeService,
        analytics_service: AnalyticsService,
        parser: QueryParser | None = None,
    ) -> None:
        self.student_service = student_service
        self.mark_service = mark_service
        self.attendance_service = attendance_service
        self.fee_service = fee_service
        self.analytics_service = analytics_service
        self.parser = parser or QueryParser()

    def execute(self, query: str) -> QueryResult:
        """Parse and execute a natural-language query."""

        parsed_query = self.parser.parse(query)

        if parsed_query.intent == QueryIntent.UNKNOWN:
            return QueryResult(
                query=query,
                parsed_query=parsed_query,
                message=(
                    "I could not understand that request. Try asking about "
                    "a student's profile, marks, attendance, fees, rank, "
                    "top students, low attendance, pending fees, or "
                    "branch toppers."
                ),
                data=None,
            )

        return self._execute_parsed_query(
            original_query=query,
            parsed_query=parsed_query,
        )

    def _execute_parsed_query(
        self,
        original_query: str,
        parsed_query: ParsedQuery,
    ) -> QueryResult:
        """Route a validated ParsedQuery to the appropriate service."""

        intent = parsed_query.intent

        if intent == QueryIntent.GET_STUDENT:
            student = self.student_service.get_student(
                parsed_query.student_id or ""
            )

            data = {
                "student_id": student.student_id,
                "name": student.name,
                "email": student.email,
                "branch": student.branch,
                "current_semester": student.current_semester,
                "section": student.section,
                "admission_year": student.admission_year,
            }

            return self._build_result(
                query=original_query,
                parsed_query=parsed_query,
                message=f"Student profile found for {student.student_id}.",
                data=data,
            )

        if intent == QueryIntent.GET_MARKS:
            records = self.mark_service.get_student_marks(
                student_id=parsed_query.student_id or "",
                semester=parsed_query.semester,
            )

            return self._build_result(
                query=original_query,
                parsed_query=parsed_query,
                message=self._record_message(
                    count=len(records),
                    singular="mark record",
                    plural="mark records",
                ),
                data=records,
            )

        if intent == QueryIntent.GET_ATTENDANCE:
            records = self.attendance_service.get_student_attendance(
                student_id=parsed_query.student_id or "",
                semester=parsed_query.semester,
            )

            return self._build_result(
                query=original_query,
                parsed_query=parsed_query,
                message=self._record_message(
                    count=len(records),
                    singular="attendance record",
                    plural="attendance records",
                ),
                data=records,
            )

        if intent == QueryIntent.GET_FEES:
            records = self.fee_service.get_student_fees(
                student_id=parsed_query.student_id or "",
                semester=parsed_query.semester,
            )

            return self._build_result(
                query=original_query,
                parsed_query=parsed_query,
                message=self._record_message(
                    count=len(records),
                    singular="fee record",
                    plural="fee records",
                ),
                data=records,
            )

        if intent == QueryIntent.GET_STUDENT_RANK:
            record = self.analytics_service.get_student_rank(
                student_id=parsed_query.student_id or "",
                semester=parsed_query.semester or 0,
            )

            return self._build_result(
                query=original_query,
                parsed_query=parsed_query,
                message=(
                    f"Rank found for {record.student_id} in semester "
                    f"{parsed_query.semester}."
                ),
                data=record,
            )

        if intent == QueryIntent.GET_TOP_STUDENTS:
            records = self.analytics_service.get_top_students(
                semester=parsed_query.semester or 0,
                limit=parsed_query.limit,
            )

            return self._build_result(
                query=original_query,
                parsed_query=parsed_query,
                message=self._record_message(
                    count=len(records),
                    singular="top student",
                    plural="top students",
                ),
                data=records,
            )

        if intent == QueryIntent.GET_LOW_ATTENDANCE:
            records = (
                self.analytics_service.get_low_attendance_students(
                    threshold=parsed_query.attendance_threshold,
                    semester=parsed_query.semester,
                )
            )

            return self._build_result(
                query=original_query,
                parsed_query=parsed_query,
                message=self._record_message(
                    count=len(records),
                    singular="student with low attendance",
                    plural="students with low attendance",
                ),
                data=records,
            )

        if intent == QueryIntent.GET_PENDING_FEES:
            records = self.analytics_service.get_pending_fee_students(
                semester=parsed_query.semester,
            )

            return self._build_result(
                query=original_query,
                parsed_query=parsed_query,
                message=self._record_message(
                    count=len(records),
                    singular="student with pending fees",
                    plural="students with pending fees",
                ),
                data=records,
            )

        if intent == QueryIntent.GET_BRANCH_TOPPERS:
            records = self.analytics_service.get_branch_toppers(
                semester=parsed_query.semester or 0,
            )

            return self._build_result(
                query=original_query,
                parsed_query=parsed_query,
                message=self._record_message(
                    count=len(records),
                    singular="branch topper",
                    plural="branch toppers",
                ),
                data=records,
            )

        return QueryResult(
            query=original_query,
            parsed_query=parsed_query,
            message="The parsed intent is not currently supported.",
            data=None,
        )

    @staticmethod
    def _build_result(
        query: str,
        parsed_query: ParsedQuery,
        message: str,
        data: object,
    ) -> QueryResult:
        """Create a JSON-safe query response."""

        return QueryResult(
            query=query,
            parsed_query=parsed_query,
            message=message,
            data=jsonable_encoder(data),
        )

    @staticmethod
    def _record_message(
        count: int,
        singular: str,
        plural: str,
    ) -> str:
        """Create a readable message based on the number of records."""

        if count == 0:
            return f"No {plural} were found."

        if count == 1:
            return f"Found 1 {singular}."

        return f"Found {count} {plural}."