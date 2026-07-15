"""Services for validating and importing school CSV files."""

from __future__ import annotations

from io import BytesIO

import pandas as pd
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.models.mark import Mark
from backend.models.student import Student
from backend.models.subject import Subject
from backend.schemas.upload import UploadRowError, UploadSummaryResponse
from backend.models.attendance import Attendance
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from backend.models.fee import Fee, FeeStatus

class CSVService:
    """Validate CSV files and import their records into the database."""

    STUDENT_REQUIRED_COLUMNS = {
        "student_id",
        "name",
        "branch",
        "current_semester",
        "admission_year",
    }

    SUBJECT_REQUIRED_COLUMNS = {
        "subject_code",
        "subject_name",
        "semester",
        "maximum_marks",
        "credit",
    }

    MARK_REQUIRED_COLUMNS = {
        "student_id",
        "subject_code",
        "semester",
        "internal_marks",
        "external_marks",
        "exam_type",
        "academic_year",
    }

    ATTENDANCE_REQUIRED_COLUMNS = {
        "student_id",
        "subject_code",
        "semester",
        "classes_held",
        "classes_attended",
        "academic_year",
    }

    FEE_REQUIRED_COLUMNS = {
        "student_id",
        "semester",
        "total_fee",
        "amount_paid",
        "status",
        "academic_year",
    }


    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def _normalize_column_name(column: object) -> str:
        """Convert a CSV column name into a consistent format."""

        return (
            str(column)
            .strip()
            .lower()
            .replace(" ", "_")
            .replace("-", "_")
        )

    @staticmethod
    def _clean_optional_string(value: object) -> str | None:
        """Convert an optional CSV value into a clean string or None."""

        if pd.isna(value):
            return None

        cleaned = str(value).strip()

        return cleaned or None

    @staticmethod
    def _clean_required_string(
        value: object,
        field_name: str,
    ) -> str:
        """Validate and clean a required text value."""

        if pd.isna(value):
            raise ValueError(f"{field_name} is required.")

        cleaned = str(value).strip()

        if not cleaned:
            raise ValueError(f"{field_name} is required.")

        return cleaned

    @staticmethod
    def _parse_integer(
        value: object,
        field_name: str,
    ) -> int:
        """Convert a CSV value into an integer."""

        if pd.isna(value):
            raise ValueError(f"{field_name} is required.")

        try:
            numeric_value = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"{field_name} must be a valid integer."
            ) from exc

        if not numeric_value.is_integer():
            raise ValueError(
                f"{field_name} must be a whole number."
            )

        return int(numeric_value)

    @staticmethod
    def _parse_float(
        value: object,
        field_name: str,
    ) -> float:
        """Convert a CSV value into a floating-point number."""

        if pd.isna(value):
            raise ValueError(f"{field_name} is required.")

        try:
            return float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"{field_name} must be a valid number."
            ) from exc

    @staticmethod
    def _parse_optional_float(
        value: object,
        field_name: str,
    ) -> float | None:
        """Convert an optional CSV value into a float or None."""

        if pd.isna(value):
            return None

        cleaned = str(value).strip()

        if not cleaned:
            return None

        try:
            return float(cleaned)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"{field_name} must be a valid number."
            ) from exc
    

    @staticmethod
    def _parse_money_to_paise(
        value: object,
        field_name: str,
    ) -> int:
        """
        Convert a rupee amount from the CSV into integer paise.

        Example: 1250.50 rupees becomes 125050 paise.
        """

        if pd.isna(value):
            raise ValueError(f"{field_name} is required.")

        cleaned = str(value).strip()

        if not cleaned:
            raise ValueError(f"{field_name} is required.")

        try:
            rupee_amount = Decimal(cleaned)
        except InvalidOperation as exc:
            raise ValueError(
                f"{field_name} must be a valid monetary amount."
            ) from exc

        if not rupee_amount.is_finite():
            raise ValueError(
                f"{field_name} must be a finite monetary amount."
            )

        if rupee_amount < 0:
            raise ValueError(
                f"{field_name} cannot be negative."
            )

        rounded_amount = rupee_amount.quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

        return int(rounded_amount * 100)


    @staticmethod
    def _parse_optional_date(
        value: object,
        field_name: str,
    ) -> date | None:
        """Parse an optional ISO date in YYYY-MM-DD format."""

        if pd.isna(value):
            return None

        cleaned = str(value).strip()

        if not cleaned:
            return None

        try:
            return date.fromisoformat(cleaned)
        except ValueError as exc:
            raise ValueError(
                f"{field_name} must use YYYY-MM-DD format."
            ) from exc

    @staticmethod
    def _calculate_grade(
        total_marks: float,
        maximum_marks: int,
    ) -> tuple[str, float]:
        """Calculate a letter grade and grade point from percentage."""

        percentage = (total_marks / maximum_marks) * 100

        if percentage >= 90:
            return "A+", 10.0
        if percentage >= 80:
            return "A", 9.0
        if percentage >= 70:
            return "B+", 8.0
        if percentage >= 60:
            return "B", 7.0
        if percentage >= 50:
            return "C", 6.0
        if percentage >= 40:
            return "D", 5.0

        return "F", 0.0

    @staticmethod
    def _validate_csv_filename(filename: str | None) -> None:
        """Ensure the uploaded file has a CSV extension."""

        if not filename:
            raise ValueError("The uploaded file must have a filename.")

        if not filename.lower().endswith(".csv"):
            raise ValueError("Only CSV files are supported.")

    def _read_csv(
        self,
        file_content: bytes,
        filename: str | None,
    ) -> pd.DataFrame:
        """Read uploaded CSV bytes into a normalized DataFrame."""

        self._validate_csv_filename(filename)

        if not file_content:
            raise ValueError("The uploaded CSV file is empty.")

        try:
            dataframe = pd.read_csv(BytesIO(file_content))
        except UnicodeDecodeError as exc:
            raise ValueError(
                "The CSV file must use UTF-8 compatible text encoding."
            ) from exc
        except pd.errors.EmptyDataError as exc:
            raise ValueError(
                "The uploaded CSV file does not contain any data."
            ) from exc
        except pd.errors.ParserError as exc:
            raise ValueError(
                "The uploaded file could not be parsed as a valid CSV."
            ) from exc

        dataframe.columns = [
            self._normalize_column_name(column)
            for column in dataframe.columns
        ]

        return dataframe

    @staticmethod
    def _validate_required_columns(
        dataframe: pd.DataFrame,
        required_columns: set[str],
    ) -> None:
        """Check that all required columns exist in a DataFrame."""

        available_columns = set(dataframe.columns)
        missing_columns = required_columns - available_columns

        if missing_columns:
            formatted_columns = ", ".join(sorted(missing_columns))

            raise ValueError(
                f"Missing required CSV columns: {formatted_columns}."
            )

    def import_students(
        self,
        file_content: bytes,
        filename: str | None,
        replace_existing: bool = False,
    ) -> UploadSummaryResponse:
        """
        Validate and import students from a CSV file.

        Existing records are skipped unless replace_existing is true.
        """

        dataframe = self._read_csv(
            file_content=file_content,
            filename=filename,
        )

        self._validate_required_columns(
            dataframe=dataframe,
            required_columns=self.STUDENT_REQUIRED_COLUMNS,
        )

        total_rows = len(dataframe)
        inserted_rows = 0
        updated_rows = 0
        skipped_rows = 0
        errors: list[UploadRowError] = []

        try:
            for dataframe_index, row in dataframe.iterrows():
                csv_row_number = int(dataframe_index) + 2

                try:
                    student_id = self._clean_required_string(
                        row.get("student_id"),
                        "student_id",
                    ).upper()

                    name = self._clean_required_string(
                        row.get("name"),
                        "name",
                    )

                    branch = self._clean_required_string(
                        row.get("branch"),
                        "branch",
                    ).upper()

                    current_semester = self._parse_integer(
                        row.get("current_semester"),
                        "current_semester",
                    )

                    admission_year = self._parse_integer(
                        row.get("admission_year"),
                        "admission_year",
                    )

                    email = self._clean_optional_string(
                        row.get("email")
                    )

                    if email is not None:
                        email = email.lower()

                    section = self._clean_optional_string(
                        row.get("section")
                    )

                    if section is not None:
                        section = section.upper()

                    if not 1 <= current_semester <= 8:
                        raise ValueError(
                            "current_semester must be between 1 and 8."
                        )

                    if not 1900 <= admission_year <= 2100:
                        raise ValueError(
                            "admission_year must be between 1900 and 2100."
                        )

                    existing_student = self.db.scalar(
                        select(Student).where(
                            Student.student_id == student_id
                        )
                    )

                    if existing_student is not None:
                        if not replace_existing:
                            skipped_rows += 1
                            continue

                        existing_student.name = name
                        existing_student.email = email
                        existing_student.branch = branch
                        existing_student.current_semester = (
                            current_semester
                        )
                        existing_student.section = section
                        existing_student.admission_year = admission_year

                        updated_rows += 1
                        continue

                    student = Student(
                        student_id=student_id,
                        name=name,
                        email=email,
                        branch=branch,
                        current_semester=current_semester,
                        section=section,
                        admission_year=admission_year,
                    )

                    self.db.add(student)
                    inserted_rows += 1

                except ValueError as exc:
                    errors.append(
                        UploadRowError(
                            row=csv_row_number,
                            field=None,
                            message=str(exc),
                        )
                    )

            self.db.commit()

        except IntegrityError as exc:
            self.db.rollback()

            raise ValueError(
                "The CSV contains duplicate or conflicting student data, "
                "such as an email already assigned to another student."
            ) from exc

        except Exception:
            self.db.rollback()
            raise

        return UploadSummaryResponse(
            file_type="students",
            total_rows=total_rows,
            inserted_rows=inserted_rows,
            updated_rows=updated_rows,
            skipped_rows=skipped_rows,
            failed_rows=len(errors),
            errors=errors,
        )

    def import_subjects(
        self,
        file_content: bytes,
        filename: str | None,
        replace_existing: bool = False,
    ) -> UploadSummaryResponse:
        """
        Validate and import subjects from a CSV file.

        Existing subjects are skipped unless replace_existing is true.
        """

        dataframe = self._read_csv(
            file_content=file_content,
            filename=filename,
        )

        self._validate_required_columns(
            dataframe=dataframe,
            required_columns=self.SUBJECT_REQUIRED_COLUMNS,
        )

        total_rows = len(dataframe)
        inserted_rows = 0
        updated_rows = 0
        skipped_rows = 0
        errors: list[UploadRowError] = []

        try:
            for dataframe_index, row in dataframe.iterrows():
                csv_row_number = int(dataframe_index) + 2

                try:
                    subject_code = self._clean_required_string(
                        row.get("subject_code"),
                        "subject_code",
                    ).upper()

                    subject_name = self._clean_required_string(
                        row.get("subject_name"),
                        "subject_name",
                    )

                    semester = self._parse_integer(
                        row.get("semester"),
                        "semester",
                    )

                    maximum_marks = self._parse_integer(
                        row.get("maximum_marks"),
                        "maximum_marks",
                    )

                    credit = self._parse_float(
                        row.get("credit"),
                        "credit",
                    )

                    if not 1 <= semester <= 8:
                        raise ValueError(
                            "semester must be between 1 and 8."
                        )

                    if maximum_marks <= 0:
                        raise ValueError(
                            "maximum_marks must be greater than 0."
                        )

                    if credit <= 0:
                        raise ValueError(
                            "credit must be greater than 0."
                        )

                    existing_subject = self.db.scalar(
                        select(Subject).where(
                            Subject.subject_code == subject_code
                        )
                    )

                    if existing_subject is not None:
                        if not replace_existing:
                            skipped_rows += 1
                            continue

                        existing_subject.subject_name = subject_name
                        existing_subject.semester = semester
                        existing_subject.maximum_marks = maximum_marks
                        existing_subject.credit = credit

                        updated_rows += 1
                        continue

                    subject = Subject(
                        subject_code=subject_code,
                        subject_name=subject_name,
                        semester=semester,
                        maximum_marks=maximum_marks,
                        credit=credit,
                    )

                    self.db.add(subject)
                    inserted_rows += 1

                except ValueError as exc:
                    errors.append(
                        UploadRowError(
                            row=csv_row_number,
                            field=None,
                            message=str(exc),
                        )
                    )

            self.db.commit()

        except IntegrityError as exc:
            self.db.rollback()

            raise ValueError(
                "The CSV contains duplicate or conflicting subject data."
            ) from exc

        except Exception:
            self.db.rollback()
            raise

        return UploadSummaryResponse(
            file_type="subjects",
            total_rows=total_rows,
            inserted_rows=inserted_rows,
            updated_rows=updated_rows,
            skipped_rows=skipped_rows,
            failed_rows=len(errors),
            errors=errors,
        )

    def import_marks(
        self,
        file_content: bytes,
        filename: str | None,
        replace_existing: bool = False,
    ) -> UploadSummaryResponse:
        """
        Validate and import student marks from a CSV file.

        Students and subjects must already exist. A mark record is uniquely
        identified by student, subject, semester, examination type, and
        academic year.
        """

        dataframe = self._read_csv(
            file_content=file_content,
            filename=filename,
        )

        self._validate_required_columns(
            dataframe=dataframe,
            required_columns=self.MARK_REQUIRED_COLUMNS,
        )

        total_rows = len(dataframe)
        inserted_rows = 0
        updated_rows = 0
        skipped_rows = 0
        errors: list[UploadRowError] = []

        try:
            for dataframe_index, row in dataframe.iterrows():
                csv_row_number = int(dataframe_index) + 2

                try:
                    student_school_id = self._clean_required_string(
                        row.get("student_id"),
                        "student_id",
                    ).upper()

                    subject_code = self._clean_required_string(
                        row.get("subject_code"),
                        "subject_code",
                    ).upper()

                    semester = self._parse_integer(
                        row.get("semester"),
                        "semester",
                    )

                    internal_marks = self._parse_float(
                        row.get("internal_marks"),
                        "internal_marks",
                    )

                    external_marks = self._parse_float(
                        row.get("external_marks"),
                        "external_marks",
                    )

                    exam_type = self._clean_required_string(
                        row.get("exam_type"),
                        "exam_type",
                    ).upper()

                    academic_year = self._clean_required_string(
                        row.get("academic_year"),
                        "academic_year",
                    )

                    if not 1 <= semester <= 8:
                        raise ValueError(
                            "semester must be between 1 and 8."
                        )

                    if internal_marks < 0:
                        raise ValueError(
                            "internal_marks cannot be negative."
                        )

                    if external_marks < 0:
                        raise ValueError(
                            "external_marks cannot be negative."
                        )

                    student = self.db.scalar(
                        select(Student).where(
                            Student.student_id == student_school_id
                        )
                    )

                    if student is None:
                        raise ValueError(
                            f"Student '{student_school_id}' does not exist."
                        )

                    subject = self.db.scalar(
                        select(Subject).where(
                            Subject.subject_code == subject_code
                        )
                    )

                    if subject is None:
                        raise ValueError(
                            f"Subject '{subject_code}' does not exist."
                        )

                    if subject.semester != semester:
                        raise ValueError(
                            f"Subject '{subject_code}' belongs to semester "
                            f"{subject.semester}, not semester {semester}."
                        )

                    total_marks = round(
                        internal_marks + external_marks,
                        2,
                    )

                    if total_marks > subject.maximum_marks:
                        raise ValueError(
                            f"total_marks cannot exceed the subject maximum "
                            f"of {subject.maximum_marks}."
                        )

                    grade = self._clean_optional_string(
                        row.get("grade")
                    )

                    if grade is not None:
                        grade = grade.upper()

                    grade_point = self._parse_optional_float(
                        row.get("grade_point"),
                        "grade_point",
                    )

                    calculated_grade, calculated_grade_point = (
                        self._calculate_grade(
                            total_marks=total_marks,
                            maximum_marks=subject.maximum_marks,
                        )
                    )

                    if grade is None:
                        grade = calculated_grade

                    if grade_point is None:
                        grade_point = calculated_grade_point

                    if not 0 <= grade_point <= 10:
                        raise ValueError(
                            "grade_point must be between 0 and 10."
                        )

                    existing_mark = self.db.scalar(
                        select(Mark).where(
                            Mark.student_id == student.id,
                            Mark.subject_id == subject.id,
                            Mark.semester == semester,
                            Mark.exam_type == exam_type,
                            Mark.academic_year == academic_year,
                        )
                    )

                    if existing_mark is not None:
                        if not replace_existing:
                            skipped_rows += 1
                            continue

                        existing_mark.internal_marks = internal_marks
                        existing_mark.external_marks = external_marks
                        existing_mark.total_marks = total_marks
                        existing_mark.grade = grade
                        existing_mark.grade_point = grade_point

                        updated_rows += 1
                        continue

                    mark = Mark(
                        student_id=student.id,
                        subject_id=subject.id,
                        semester=semester,
                        internal_marks=internal_marks,
                        external_marks=external_marks,
                        total_marks=total_marks,
                        grade=grade,
                        grade_point=grade_point,
                        exam_type=exam_type,
                        academic_year=academic_year,
                    )

                    self.db.add(mark)
                    inserted_rows += 1

                except ValueError as exc:
                    errors.append(
                        UploadRowError(
                            row=csv_row_number,
                            field=None,
                            message=str(exc),
                        )
                    )

            self.db.commit()

        except IntegrityError as exc:
            self.db.rollback()

            raise ValueError(
                "The CSV contains duplicate or conflicting mark records."
            ) from exc

        except Exception:
            self.db.rollback()
            raise

        return UploadSummaryResponse(
            file_type="marks",
            total_rows=total_rows,
            inserted_rows=inserted_rows,
            updated_rows=updated_rows,
            skipped_rows=skipped_rows,
            failed_rows=len(errors),
            errors=errors,
        )
    
    def import_attendance(
        self,
        file_content: bytes,
        filename: str | None,
        replace_existing: bool = False,
    ) -> UploadSummaryResponse:
        """
        Validate and import subject-level attendance records.
        Students and subjects must already exist. An attendance record is
        uniquely identified by student, subject, semester, and academic year.
        """

        dataframe = self._read_csv(
            file_content=file_content,
            filename=filename,
        )

        self._validate_required_columns(
            dataframe=dataframe,
            required_columns=self.ATTENDANCE_REQUIRED_COLUMNS,
        )

        total_rows = len(dataframe)
        inserted_rows = 0
        updated_rows = 0
        skipped_rows = 0
        errors: list[UploadRowError] = []

        try:
            for dataframe_index, row in dataframe.iterrows():
                csv_row_number = int(dataframe_index) + 2

                try:
                    student_school_id = self._clean_required_string(
                        row.get("student_id"),
                        "student_id",
                    ).upper()

                    subject_code = self._clean_required_string(
                        row.get("subject_code"),
                        "subject_code",
                    ).upper()

                    semester = self._parse_integer(
                        row.get("semester"),
                        "semester",
                    )

                    classes_held = self._parse_integer(
                        row.get("classes_held"),
                        "classes_held",
                    )

                    classes_attended = self._parse_integer(
                        row.get("classes_attended"),
                        "classes_attended",
                    )

                    academic_year = self._clean_required_string(
                        row.get("academic_year"),
                        "academic_year",
                    )

                    if not 1 <= semester <= 8:
                        raise ValueError(
                            "semester must be between 1 and 8."
                        )

                    if classes_held < 0:
                        raise ValueError(
                            "classes_held cannot be negative."
                        )

                    if classes_attended < 0:
                        raise ValueError(
                            "classes_attended cannot be negative."
                        )

                    if classes_attended > classes_held:
                        raise ValueError(
                            "classes_attended cannot exceed classes_held."
                        )

                    student = self.db.scalar(
                        select(Student).where(
                            Student.student_id == student_school_id
                        )
                    )

                    if student is None:
                        raise ValueError(
                            f"Student '{student_school_id}' does not exist."
                        )

                    subject = self.db.scalar(
                        select(Subject).where(
                            Subject.subject_code == subject_code
                        )
                    )

                    if subject is None:
                        raise ValueError(
                            f"Subject '{subject_code}' does not exist."
                        )

                    if subject.semester != semester:
                        raise ValueError(
                            f"Subject '{subject_code}' belongs to semester "
                            f"{subject.semester}, not semester {semester}."
                        )

                    attendance_percentage = (
                        round(
                            (classes_attended / classes_held) * 100,
                            2,
                        )
                        if classes_held > 0
                        else 0.0
                    )

                    existing_attendance = self.db.scalar(
                        select(Attendance).where(
                            Attendance.student_id == student.id,
                            Attendance.subject_id == subject.id,
                            Attendance.semester == semester,
                            Attendance.academic_year == academic_year,
                        )
                    )

                    if existing_attendance is not None:
                        if not replace_existing:
                            skipped_rows += 1
                            continue

                        existing_attendance.classes_held = classes_held
                        existing_attendance.classes_attended = (
                            classes_attended
                        )
                        existing_attendance.attendance_percentage = (
                            attendance_percentage
                        )

                        updated_rows += 1
                        continue

                    attendance = Attendance(
                        student_id=student.id,
                        subject_id=subject.id,
                        semester=semester,
                        classes_held=classes_held,
                        classes_attended=classes_attended,
                        attendance_percentage=attendance_percentage,
                        academic_year=academic_year,
                    )

                    self.db.add(attendance)
                    inserted_rows += 1

                except ValueError as exc:
                    errors.append(
                        UploadRowError(
                            row=csv_row_number,
                            field=None,
                            message=str(exc),
                        )
                    )

            self.db.commit()

        except IntegrityError as exc:
            self.db.rollback()

            raise ValueError(
                "The CSV contains duplicate or conflicting "
                "attendance records."
            ) from exc

        except Exception:
            self.db.rollback()
            raise

        return UploadSummaryResponse(
            file_type="attendance",
            total_rows=total_rows,
            inserted_rows=inserted_rows,
            updated_rows=updated_rows,
            skipped_rows=skipped_rows,
            failed_rows=len(errors),
            errors=errors,
        )
    
    def import_fees(
        self,
        file_content: bytes,
        filename: str | None,
        replace_existing: bool = False,
    ) -> UploadSummaryResponse:
        """
        Validate and import student fee records.

        A fee record is uniquely identified by student, semester,
        and academic year. CSV monetary values are provided in rupees
        and stored in the database as integer paise.
        """

        dataframe = self._read_csv(
            file_content=file_content,
            filename=filename,
        )

        self._validate_required_columns(
            dataframe=dataframe,
            required_columns=self.FEE_REQUIRED_COLUMNS,
        )

        total_rows = len(dataframe)
        inserted_rows = 0
        updated_rows = 0
        skipped_rows = 0
        errors: list[UploadRowError] = []

        try:
            for dataframe_index, row in dataframe.iterrows():
                csv_row_number = int(dataframe_index) + 2

                try:
                    student_school_id = self._clean_required_string(
                        row.get("student_id"),
                        "student_id",
                    ).upper()

                    semester = self._parse_integer(
                        row.get("semester"),
                        "semester",
                    )

                    total_fee = self._parse_money_to_paise(
                        row.get("total_fee"),
                        "total_fee",
                    )

                    amount_paid = self._parse_money_to_paise(
                        row.get("amount_paid"),
                        "amount_paid",
                    )

                    status_value = self._clean_required_string(
                        row.get("status"),
                        "status",
                    ).upper()

                    academic_year = self._clean_required_string(
                        row.get("academic_year"),
                        "academic_year",
                    )

                    due_date = self._parse_optional_date(
                        row.get("due_date"),
                        "due_date",
                    )

                    payment_date = self._parse_optional_date(
                        row.get("payment_date"),
                        "payment_date",
                    )

                    if not 1 <= semester <= 8:
                        raise ValueError(
                            "semester must be between 1 and 8."
                        )

                    if amount_paid > total_fee:
                        raise ValueError(
                            "amount_paid cannot exceed total_fee."
                        )

                    try:
                        fee_status = FeeStatus(status_value)
                    except ValueError as exc:
                        allowed_statuses = ", ".join(
                            status.value for status in FeeStatus
                        )

                        raise ValueError(
                            f"status must be one of: {allowed_statuses}."
                        ) from exc

                    amount_due = total_fee - amount_paid

                    if fee_status == FeeStatus.PAID and amount_due != 0:
                        raise ValueError(
                            "PAID status requires amount_paid to equal "
                            "total_fee."
                        )

                    if (
                        fee_status == FeeStatus.PARTIALLY_PAID
                        and not 0 < amount_paid < total_fee
                    ):
                        raise ValueError(
                            "PARTIALLY_PAID status requires amount_paid "
                            "to be greater than 0 and less than total_fee."
                        )

                    if (
                        fee_status in {
                            FeeStatus.PENDING,
                            FeeStatus.OVERDUE,
                        }
                        and amount_due == 0
                    ):
                        raise ValueError(
                            f"{fee_status.value} status requires an "
                            "outstanding amount."
                        )

                    if payment_date is not None and amount_paid == 0:
                        raise ValueError(
                            "payment_date cannot be provided when "
                            "amount_paid is 0."
                        )

                    student = self.db.scalar(
                        select(Student).where(
                            Student.student_id == student_school_id
                        )
                    )

                    if student is None:
                        raise ValueError(
                            f"Student '{student_school_id}' does not exist."
                        )

                    existing_fee = self.db.scalar(
                        select(Fee).where(
                            Fee.student_id == student.id,
                            Fee.semester == semester,
                            Fee.academic_year == academic_year,
                        )
                    )

                    if existing_fee is not None:
                        if not replace_existing:
                            skipped_rows += 1
                            continue

                        existing_fee.total_fee = total_fee
                        existing_fee.amount_paid = amount_paid
                        existing_fee.amount_due = amount_due
                        existing_fee.status = fee_status
                        existing_fee.due_date = due_date
                        existing_fee.payment_date = payment_date

                        updated_rows += 1
                        continue

                    fee = Fee(
                        student_id=student.id,
                        semester=semester,
                        total_fee=total_fee,
                        amount_paid=amount_paid,
                        amount_due=amount_due,
                        status=fee_status,
                        due_date=due_date,
                        payment_date=payment_date,
                        academic_year=academic_year,
                    )

                    self.db.add(fee)
                    inserted_rows += 1

                except ValueError as exc:
                    errors.append(
                        UploadRowError(
                            row=csv_row_number,
                            field=None,
                            message=str(exc),
                        )
                    )

            self.db.commit()

        except IntegrityError as exc:
            self.db.rollback()

            raise ValueError(
                "The CSV contains duplicate or conflicting fee records."
            ) from exc

        except Exception:
            self.db.rollback()
            raise

        return UploadSummaryResponse(
            file_type="fees",
            total_rows=total_rows,
            inserted_rows=inserted_rows,
            updated_rows=updated_rows,
            skipped_rows=skipped_rows,
            failed_rows=len(errors),
            errors=errors,
        )