"""Human-readable response formatting for natural-language queries."""

from __future__ import annotations

from typing import Any

from backend.llm.schemas import ParsedQuery, QueryIntent


class QueryAnswerFormatter:
    """Convert structured query results into readable answers."""

    def format(
        self,
        parsed_query: ParsedQuery,
        data: Any,
    ) -> str:
        """Return a human-readable answer for a supported query intent."""

        intent = parsed_query.intent

        if intent == QueryIntent.GET_STUDENT:
            return self._format_student(data)

        if intent == QueryIntent.GET_MARKS:
            return self._format_marks(
                student_id=parsed_query.student_id,
                semester=parsed_query.semester,
                records=data,
            )

        if intent == QueryIntent.GET_ATTENDANCE:
            return self._format_attendance(
                student_id=parsed_query.student_id,
                semester=parsed_query.semester,
                records=data,
            )

        if intent == QueryIntent.GET_FEES:
            return self._format_fees(
                student_id=parsed_query.student_id,
                semester=parsed_query.semester,
                records=data,
            )

        if intent == QueryIntent.GET_STUDENT_RANK:
            return self._format_student_rank(
                semester=parsed_query.semester,
                record=data,
            )

        if intent == QueryIntent.GET_TOP_STUDENTS:
            return self._format_top_students(
                semester=parsed_query.semester,
                records=data,
            )

        if intent == QueryIntent.GET_LOW_ATTENDANCE:
            return self._format_low_attendance(
                threshold=parsed_query.attendance_threshold,
                semester=parsed_query.semester,
                records=data,
            )

        if intent == QueryIntent.GET_PENDING_FEES:
            return self._format_pending_fees(
                semester=parsed_query.semester,
                records=data,
            )

        if intent == QueryIntent.GET_BRANCH_TOPPERS:
            return self._format_branch_toppers(
                semester=parsed_query.semester,
                records=data,
            )

        return (
            "I could not understand that request. Ask about student profiles, "
            "marks, attendance, fees, ranks, toppers, or related analytics."
        )

    @staticmethod
    def _format_student(data: Any) -> str:
        """Format a student profile."""

        if not isinstance(data, dict):
            return "The student profile could not be formatted."

        student_id = data.get("student_id", "Unknown")
        name = data.get("name", "Unknown")
        branch = data.get("branch", "Unknown")
        semester = data.get("current_semester", "Unknown")
        section = data.get("section")

        answer = (
            f"{student_id} is {name}, enrolled in the {branch} branch "
            f"and currently studying in semester {semester}"
        )

        if section:
            answer += f", section {section}"

        return answer + "."

    @staticmethod
    def _format_marks(
        student_id: str | None,
        semester: int | None,
        records: Any,
    ) -> str:
        """Format student marks."""

        if not records:
            semester_text = (
                f" for semester {semester}"
                if semester is not None
                else ""
            )

            return (
                f"No mark records were found for "
                f"{student_id or 'the student'}{semester_text}."
            )

        lines: list[str] = []

        for record in records:
            if not isinstance(record, dict):
                continue

            subject_name = record.get("subject_name", "Unknown subject")
            total_marks = record.get("total_marks", "Unknown")
            grade = record.get("grade", "Unknown")

            lines.append(
                f"{subject_name}: {total_marks} marks, grade {grade}"
            )

        semester_text = (
            f" in semester {semester}"
            if semester is not None
            else ""
        )

        if not lines:
            return "The mark records could not be formatted."

        return (
            f"{student_id or 'The student'} has the following results"
            f"{semester_text}: "
            + "; ".join(lines)
            + "."
        )

    @staticmethod
    def _format_attendance(
        student_id: str | None,
        semester: int | None,
        records: Any,
    ) -> str:
        """Format attendance records."""

        if not records:
            semester_text = (
                f" for semester {semester}"
                if semester is not None
                else ""
            )

            return (
                f"No attendance records were found for "
                f"{student_id or 'the student'}{semester_text}."
            )

        lines: list[str] = []

        for record in records:
            if not isinstance(record, dict):
                continue

            subject_name = record.get("subject_name") or "Overall"
            percentage = record.get(
                "attendance_percentage",
                "Unknown",
            )

            lines.append(
                f"{subject_name}: {percentage}%"
            )

        semester_text = (
            f" in semester {semester}"
            if semester is not None
            else ""
        )

        return (
            f"{student_id or 'The student'} has the following attendance"
            f"{semester_text}: "
            + "; ".join(lines)
            + "."
        )

    @staticmethod
    def _format_fees(
        student_id: str | None,
        semester: int | None,
        records: Any,
    ) -> str:
        """Format fee records."""

        if not records:
            semester_text = (
                f" for semester {semester}"
                if semester is not None
                else ""
            )

            return (
                f"No fee records were found for "
                f"{student_id or 'the student'}{semester_text}."
            )

        lines: list[str] = []

        for record in records:
            if not isinstance(record, dict):
                continue

            record_semester = record.get("semester", semester)
            amount_due_paise = record.get("amount_due", 0)
            status = record.get("status", "Unknown")

            try:
                amount_due_rupees = float(amount_due_paise) / 100
                amount_text = f"₹{amount_due_rupees:,.2f}"
            except (TypeError, ValueError):
                amount_text = "an unknown amount"

            lines.append(
                f"semester {record_semester}: {amount_text} due, "
                f"status {status}"
            )

        return (
            f"Fee details for {student_id or 'the student'}: "
            + "; ".join(lines)
            + "."
        )

    @staticmethod
    def _format_student_rank(
        semester: int | None,
        record: Any,
    ) -> str:
        """Format a student rank result."""

        if not isinstance(record, dict):
            return "The student rank could not be formatted."

        student_id = record.get("student_id", "The student")
        rank = record.get("rank", "Unknown")
        average_marks = record.get("average_marks", "Unknown")

        return (
            f"{student_id} is ranked {rank} in semester {semester}, "
            f"with an average score of {average_marks}."
        )

    @staticmethod
    def _format_top_students(
        semester: int | None,
        records: Any,
    ) -> str:
        """Format top-student results."""

        if not records:
            return (
                f"No ranked students were found for semester {semester}."
            )

        lines: list[str] = []

        for record in records:
            if not isinstance(record, dict):
                continue

            rank = record.get("rank", "Unknown")
            student_id = record.get("student_id", "Unknown")
            name = record.get("student_name", "Unknown")
            average = record.get("average_marks", "Unknown")

            lines.append(
                f"{rank}. {name} ({student_id}) — {average}"
            )

        return (
            f"Top students for semester {semester}: "
            + "; ".join(lines)
            + "."
        )

    @staticmethod
    def _format_low_attendance(
        threshold: float,
        semester: int | None,
        records: Any,
    ) -> str:
        """Format low-attendance analytics."""

        if not records:
            semester_text = (
                f" in semester {semester}"
                if semester is not None
                else ""
            )

            return (
                f"No students were found below {threshold}% attendance"
                f"{semester_text}."
            )

        lines: list[str] = []

        for record in records:
            if not isinstance(record, dict):
                continue

            student_id = record.get("student_id", "Unknown")
            name = record.get("student_name", "Unknown")
            percentage = record.get(
                "attendance_percentage",
                "Unknown",
            )

            lines.append(
                f"{name} ({student_id}) — {percentage}%"
            )

        return (
            f"Students below {threshold}% attendance: "
            + "; ".join(lines)
            + "."
        )

    @staticmethod
    def _format_pending_fees(
        semester: int | None,
        records: Any,
    ) -> str:
        """Format pending-fee analytics."""

        if not records:
            semester_text = (
                f" for semester {semester}"
                if semester is not None
                else ""
            )

            return f"No pending fee records were found{semester_text}."

        lines: list[str] = []

        for record in records:
            if not isinstance(record, dict):
                continue

            student_id = record.get("student_id", "Unknown")
            name = record.get("student_name", "Unknown")
            amount_due_paise = record.get("amount_due", 0)

            try:
                amount_due_rupees = float(amount_due_paise) / 100
                amount_text = f"₹{amount_due_rupees:,.2f}"
            except (TypeError, ValueError):
                amount_text = "an unknown amount"

            lines.append(
                f"{name} ({student_id}) — {amount_text} due"
            )

        return "Students with pending fees: " + "; ".join(lines) + "."

    @staticmethod
    def _format_branch_toppers(
        semester: int | None,
        records: Any,
    ) -> str:
        """Format branch-topper analytics."""

        if not records:
            return (
                f"No branch toppers were found for semester {semester}."
            )

        lines: list[str] = []

        for record in records:
            if not isinstance(record, dict):
                continue

            branch = record.get("branch", "Unknown")
            student_id = record.get("student_id", "Unknown")
            name = record.get("student_name", "Unknown")
            average = record.get("average_marks", "Unknown")

            lines.append(
                f"{branch}: {name} ({student_id}) — {average}"
            )

        return (
            f"Branch toppers for semester {semester}: "
            + "; ".join(lines)
            + "."
        )