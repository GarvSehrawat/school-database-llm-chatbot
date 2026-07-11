from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base

if TYPE_CHECKING:
    from backend.models.attendance import Attendance
    from backend.models.fee import Fee
    from backend.models.mark import Mark


def utc_now() -> datetime:
    """Return the current timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


class Student(Base):
    """Represents a student registered in the school database."""

    __tablename__ = "students"
    __table_args__ = (
        CheckConstraint(
            "current_semester BETWEEN 1 AND 8",
            name="ck_students_current_semester",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    student_id: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        index=True,
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False,
    )

    email: Mapped[str | None] = mapped_column(
        String(150),
        unique=True,
        nullable=True,
    )

    branch: Mapped[str] = mapped_column(
        String(30),
        index=True,
        nullable=False,
    )

    current_semester: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    section: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
    )

    admission_year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    marks: Mapped[list["Mark"]] = relationship(
        back_populates="student",
        cascade="all, delete-orphan",
    )

    attendance_records: Mapped[list["Attendance"]] = relationship(
        back_populates="student",
        cascade="all, delete-orphan",
    )

    fee_records: Mapped[list["Fee"]] = relationship(
        back_populates="student",
        cascade="all, delete-orphan",
    )