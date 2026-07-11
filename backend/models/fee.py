from datetime import date
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    Enum as SqlEnum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base

if TYPE_CHECKING:
    from backend.models.student import Student


class FeeStatus(str, Enum):
    """Allowed states for a student's fee record."""

    PAID = "PAID"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    PENDING = "PENDING"
    OVERDUE = "OVERDUE"


class Fee(Base):
    """Stores semester fee and payment information for a student."""

    __tablename__ = "fees"
    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "semester",
            "academic_year",
            name="uq_fees_student_semester_year",
        ),
        CheckConstraint(
            "semester BETWEEN 1 AND 8",
            name="ck_fees_semester",
        ),
        CheckConstraint(
            "total_fee >= 0",
            name="ck_fees_total_non_negative",
        ),
        CheckConstraint(
            "amount_paid >= 0",
            name="ck_fees_paid_non_negative",
        ),
        CheckConstraint(
            "amount_due >= 0",
            name="ck_fees_due_non_negative",
        ),
        CheckConstraint(
            "amount_paid <= total_fee",
            name="ck_fees_paid_not_above_total",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    semester: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # Monetary values are stored as integer paise.
    total_fee: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    amount_paid: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    amount_due: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    status: Mapped[FeeStatus] = mapped_column(
        SqlEnum(FeeStatus, native_enum=False),
        default=FeeStatus.PENDING,
        index=True,
        nullable=False,
    )

    due_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    payment_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    academic_year: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    student: Mapped["Student"] = relationship(
        back_populates="fee_records",
    )