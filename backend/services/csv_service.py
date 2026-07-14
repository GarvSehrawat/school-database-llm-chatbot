"""Services for validating and importing school CSV files."""

from __future__ import annotations

from io import BytesIO

import pandas as pd
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.models.student import Student
from backend.models.subject import Subject
from backend.schemas.upload import UploadRowError, UploadSummaryResponse


class CSVService:
    """Validate CSV files and import their records into the database."""

    STUDENT_REQUIRED_COLUMNS = {
        "student_id",
        "name",
        "branch",
        "current_semester",
        "admission_year",
    }

    STUDENT_OPTIONAL_COLUMNS = {
        "email",
        "section",
    }

    SUBJECT_REQUIRED_COLUMNS = {
        "subject_code",
        "subject_name",
        "semester",
        "maximum_marks",
        "credit",
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