from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base

if TYPE_CHECKING:
    from backend.models.student import Student
    from backend.models.subject import Subject


class Mark(Base):
    """Stores a student's marks for a subject and examination."""

    __tablename__ = "marks"
    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "subject_id",
            "semester",
            "exam_type",
            "academic_year",
            name="uq_marks_student_subject_exam",
        ),
        CheckConstraint(
            "semester BETWEEN 1 AND 8",
            name="ck_marks_semester",
        ),
        CheckConstraint(
            "internal_marks >= 0",
            name="ck_marks_internal_non_negative",
        ),
        CheckConstraint(
            "external_marks >= 0",
            name="ck_marks_external_non_negative",
        ),
        CheckConstraint(
            "total_marks >= 0",
            name="ck_marks_total_non_negative",
        ),
        CheckConstraint(
            "grade_point >= 0 AND grade_point <= 10",
            name="ck_marks_grade_point",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    subject_id: Mapped[int] = mapped_column(
        ForeignKey("subjects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    semester: Mapped[int] = mapped_column(
        Integer,
        index=True,
        nullable=False,
    )

    internal_marks: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )

    external_marks: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )

    total_marks: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    grade: Mapped[str | None] = mapped_column(
        String(5),
        nullable=True,
    )

    grade_point: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    exam_type: Mapped[str] = mapped_column(
        String(30),
        default="END_SEMESTER",
        nullable=False,
    )

    academic_year: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    student: Mapped["Student"] = relationship(
        back_populates="marks",
    )

    subject: Mapped["Subject"] = relationship(
        back_populates="marks",
    )