"""Tests for the deterministic natural-language query parser."""

import pytest
from pydantic import ValidationError

from backend.llm.parser import QueryParser
from backend.llm.schemas import QueryIntent


@pytest.fixture
def parser() -> QueryParser:
    """Provide a fresh query parser for each test."""

    return QueryParser()


def test_parse_student_marks_query(parser: QueryParser) -> None:
    """Parse a marks request containing student ID and semester."""

    result = parser.parse(
        "Show semester 2 marks of STU121"
    )

    assert result.intent == QueryIntent.GET_MARKS
    assert result.student_id == "STU121"
    assert result.semester == 2


def test_parse_top_students_query(parser: QueryParser) -> None:
    """Parse a top-students analytics request."""

    result = parser.parse(
        "Show top 5 students in semester 2"
    )

    assert result.intent == QueryIntent.GET_TOP_STUDENTS
    assert result.semester == 2
    assert result.limit == 5


def test_parse_low_attendance_query(parser: QueryParser) -> None:
    """Parse a low-attendance threshold request."""

    result = parser.parse(
        "Show students with attendance below 70 percent"
    )

    assert result.intent == QueryIntent.GET_LOW_ATTENDANCE
    assert result.attendance_threshold == 70.0


def test_parse_pending_fees_query(parser: QueryParser) -> None:
    """Parse a pending-fees request."""

    result = parser.parse(
        "Show pending fees for semester 2"
    )

    assert result.intent == QueryIntent.GET_PENDING_FEES
    assert result.semester == 2


def test_parse_unknown_query(parser: QueryParser) -> None:
    """Return UNKNOWN for unsupported questions."""

    result = parser.parse(
        "Tell me a joke"
    )

    assert result.intent == QueryIntent.UNKNOWN


def test_marks_query_requires_student_id(
    parser: QueryParser,
) -> None:
    """Reject a marks request that does not contain a student ID."""

    with pytest.raises(ValidationError):
        parser.parse("Show marks")