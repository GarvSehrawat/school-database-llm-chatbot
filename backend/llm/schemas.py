"""Pydantic schemas used by the natural-language query layer."""

from enum import Enum

from pydantic import BaseModel, Field, model_validator


class QueryIntent(str, Enum):
    """Supported operations that users can request using natural language."""

    GET_STUDENT = "get_student"
    GET_MARKS = "get_marks"
    GET_ATTENDANCE = "get_attendance"
    GET_FEES = "get_fees"
    GET_STUDENT_RANK = "get_student_rank"
    GET_TOP_STUDENTS = "get_top_students"
    GET_LOW_ATTENDANCE = "get_low_attendance"
    GET_PENDING_FEES = "get_pending_fees"
    GET_BRANCH_TOPPERS = "get_branch_toppers"
    UNKNOWN = "unknown"


class NaturalLanguageQueryRequest(BaseModel):
    """A natural-language question submitted by the user."""

    query: str = Field(
        min_length=2,
        max_length=500,
        examples=[
            "Show the semester 2 marks of STU121.",
        ],
    )


class ParsedQuery(BaseModel):
    """
    Structured and validated representation of a user's question.

    The future LLM will produce this object. The application will then route
    the request to predefined services instead of allowing generated SQL.
    """

    intent: QueryIntent

    student_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )

    semester: int | None = Field(
        default=None,
        ge=1,
        le=8,
    )

    branch: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )

    limit: int = Field(
        default=10,
        ge=1,
        le=100,
    )

    attendance_threshold: float = Field(
        default=75.0,
        ge=0,
        le=100,
    )

    @model_validator(mode="after")
    def validate_required_entities(self) -> "ParsedQuery":
        """Ensure each intent contains the entities it requires."""

        student_intents = {
            QueryIntent.GET_STUDENT,
            QueryIntent.GET_MARKS,
            QueryIntent.GET_ATTENDANCE,
            QueryIntent.GET_FEES,
            QueryIntent.GET_STUDENT_RANK,
        }

        semester_intents = {
            QueryIntent.GET_STUDENT_RANK,
            QueryIntent.GET_TOP_STUDENTS,
            QueryIntent.GET_BRANCH_TOPPERS,
        }

        if self.intent in student_intents and not self.student_id:
            raise ValueError(
                f"student_id is required for intent "
                f"'{self.intent.value}'."
            )

        if self.intent in semester_intents and self.semester is None:
            raise ValueError(
                f"semester is required for intent "
                f"'{self.intent.value}'."
            )

        return self


class QueryResult(BaseModel):
    """Standard response returned by the natural-language query endpoint."""

    query: str
    parsed_query: ParsedQuery
    message: str
    data: object | None = None