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


class Attendance(Base):
    """Stores overall or subject-level student attendance."""

    __tablename__ = "attendance"
    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "subject_id",
            "semester",
            "academic_year",
            name="uq_attendance_student_subject_semester",
        ),
        CheckConstraint(
            "semester BETWEEN 1 AND 8",
            name="ck_attendance_semester",
        ),
        CheckConstraint(
            "classes_held >= 0",
            name="ck_attendance_classes_held",
        ),
        CheckConstraint(
            "classes_attended >= 0",
            name="ck_attendance_classes_attended",
        ),
        CheckConstraint(
            "classes_attended <= classes_held",
            name="ck_attendance_valid_counts",
        ),
        CheckConstraint(
            "attendance_percentage >= 0 "
            "AND attendance_percentage <= 100",
            name="ck_attendance_percentage",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    subject_id: Mapped[int | None] = mapped_column(
        ForeignKey("subjects.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )

    semester: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    classes_held: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    classes_attended: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    attendance_percentage: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    academic_year: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    student: Mapped["Student"] = relationship(
        back_populates="attendance_records",
    )

    subject: Mapped["Subject | None"] = relationship(
        back_populates="attendance_records",
    )