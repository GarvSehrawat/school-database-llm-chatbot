"""Rule-based parser for supported natural-language school queries."""

from __future__ import annotations

import re

from backend.llm.schemas import ParsedQuery, QueryIntent


class QueryParser:
    """Convert simple user questions into validated structured queries."""

    STUDENT_ID_PATTERN = re.compile(r"\bSTU\d+\b", re.IGNORECASE)
    SEMESTER_PATTERN = re.compile(
        r"\b(?:semester|sem)\s*(\d+)\b",
        re.IGNORECASE,
    )
    LIMIT_PATTERN = re.compile(
        r"\b(?:top|first)\s+(\d+)\b",
        re.IGNORECASE,
    )
    THRESHOLD_PATTERN = re.compile(
        r"\b(?:below|under|less than)\s+(\d+(?:\.\d+)?)\s*%?",
        re.IGNORECASE,
    )

    def parse(self, query: str) -> ParsedQuery:
        """Parse a natural-language question into a validated ParsedQuery."""

        cleaned_query = " ".join(query.strip().split())

        if not cleaned_query:
            return ParsedQuery(intent=QueryIntent.UNKNOWN)

        lowered_query = cleaned_query.lower()

        student_id = self._extract_student_id(cleaned_query)
        semester = self._extract_semester(cleaned_query)
        limit = self._extract_limit(cleaned_query)
        threshold = self._extract_attendance_threshold(cleaned_query)
        branch = self._extract_branch(cleaned_query)

        intent = self._detect_intent(lowered_query)

        return ParsedQuery(
            intent=intent,
            student_id=student_id,
            semester=semester,
            branch=branch,
            limit=limit,
            attendance_threshold=threshold,
        )

    def _detect_intent(self, query: str) -> QueryIntent:
        """Identify the requested operation using safe predefined rules."""

        if "branch topper" in query or "branch toppers" in query:
            return QueryIntent.GET_BRANCH_TOPPERS

        if "low attendance" in query or (
            "attendance" in query
            and any(
                phrase in query
                for phrase in (
                    "below",
                    "under",
                    "less than",
                    "short attendance",
                )
            )
        ):
            return QueryIntent.GET_LOW_ATTENDANCE

        if "pending fees" in query or "unpaid fees" in query:
            return QueryIntent.GET_PENDING_FEES

        if re.search(
            r"\btop(?:\s+\d+)?\s+students?\b",
            query,
            re.IGNORECASE,
        ):
            return QueryIntent.GET_TOP_STUDENTS

        if "rank" in query:
            return QueryIntent.GET_STUDENT_RANK

        if "attendance" in query:
            return QueryIntent.GET_ATTENDANCE

        if (
            "marks" in query
            or "marksheet" in query
            or "result" in query
        ):
            return QueryIntent.GET_MARKS

        if "fee" in query or "fees" in query:
            return QueryIntent.GET_FEES

        if "student" in query or "profile" in query:
            return QueryIntent.GET_STUDENT

        return QueryIntent.UNKNOWN
        """Identify the requested operation using safe predefined rules."""

        if "branch topper" in query or "branch toppers" in query:
            return QueryIntent.GET_BRANCH_TOPPERS

        if "low attendance" in query or (
            "attendance" in query
            and any(
                phrase in query
                for phrase in (
                    "below",
                    "under",
                    "less than",
                    "short attendance",
                )
            )
        ):
            return QueryIntent.GET_LOW_ATTENDANCE

        if "pending fees" in query or "unpaid fees" in query:
            return QueryIntent.GET_PENDING_FEES

        if "top student" in query or "top students" in query:
            return QueryIntent.GET_TOP_STUDENTS

        if "rank" in query:
            return QueryIntent.GET_STUDENT_RANK

        if "attendance" in query:
            return QueryIntent.GET_ATTENDANCE

        if "marks" in query or "marksheet" in query or "result" in query:
            return QueryIntent.GET_MARKS

        if "fee" in query or "fees" in query:
            return QueryIntent.GET_FEES

        if "student" in query or "profile" in query:
            return QueryIntent.GET_STUDENT

        return QueryIntent.UNKNOWN

    def _extract_student_id(self, query: str) -> str | None:
        """Extract a student ID such as STU121."""

        match = self.STUDENT_ID_PATTERN.search(query)

        if match is None:
            return None

        return match.group(0).upper()

    def _extract_semester(self, query: str) -> int | None:
        """Extract a semester number from the query."""

        match = self.SEMESTER_PATTERN.search(query)

        if match is None:
            return None

        return int(match.group(1))

    def _extract_limit(self, query: str) -> int:
        """Extract result limit for ranking-related queries."""

        match = self.LIMIT_PATTERN.search(query)

        if match is None:
            return 10

        return int(match.group(1))

    def _extract_attendance_threshold(self, query: str) -> float:
        """Extract an attendance threshold, defaulting to 75 percent."""

        match = self.THRESHOLD_PATTERN.search(query)

        if match is None:
            return 75.0

        return float(match.group(1))

    @staticmethod
    def _extract_branch(query: str) -> str | None:
        """Extract a known branch name from the query."""

        known_branches = {
            "CSE",
            "IT",
            "ECE",
            "EEE",
            "ME",
            "CE",
        }

        query_words = {
            word.strip(".,?!:;()[]{}").upper()
            for word in query.split()
        }

        for branch in known_branches:
            if branch in query_words:
                return branch

        return None