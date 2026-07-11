from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base

if TYPE_CHECKING:
    from backend.models.attendance import Attendance
    from backend.models.mark import Mark


class Subject(Base):
    """Represents an academic subject offered in a semester."""

    __tablename__ = "subjects"
    __table_args__ = (
        CheckConstraint(
            "semester BETWEEN 1 AND 8",
            name="ck_subjects_semester",
        ),
        CheckConstraint(
            "maximum_marks > 0",
            name="ck_subjects_maximum_marks",
        ),
        CheckConstraint(
            "credit > 0",
            name="ck_subjects_credit",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    subject_code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        index=True,
        nullable=False,
    )

    subject_name: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False,
    )

    semester: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    maximum_marks: Mapped[int] = mapped_column(
        Integer,
        default=100,
        nullable=False,
    )

    credit: Mapped[float] = mapped_column(
        Float,
        default=4.0,
        nullable=False,
    )

    marks: Mapped[list["Mark"]] = relationship(
        back_populates="subject",
    )

    attendance_records: Mapped[list["Attendance"]] = relationship(
        back_populates="subject",
    )