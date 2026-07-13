"""Repository for student-related database operations."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.student import Student


class StudentRepository:
    """Handles all database operations related to students."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_student_id(self, student_id: str) -> Student | None:
        """
        Return a student using the school student_id.
        Example: STU101
        """
        stmt = select(Student).where(Student.student_id == student_id)

        return self.db.scalar(stmt)

    def get_by_name(self, name: str) -> list[Student]:
        """
        Search students by name (case-insensitive).
        """

        stmt = (
            select(Student)
            .where(Student.name.ilike(f"%{name}%"))
            .order_by(Student.name)
        )

        return list(self.db.scalars(stmt))

    def get_all(self) -> list[Student]:
        """
        Return all students.
        """

        stmt = (
            select(Student)
            .order_by(Student.student_id)
        )

        return list(self.db.scalars(stmt))