"""Populate the development database with fictional school records."""

from __future__ import annotations

import random
from datetime import date, timedelta

from sqlalchemy import delete, select

from backend.database import SessionLocal, create_database_tables
from backend.models import Attendance, Fee, FeeStatus, Mark, Student, Subject


ACADEMIC_YEAR = "2025-2026"
RANDOM_SEED = 42


STUDENT_DATA = [
    ("STU101", "Rahul Sharma", "rahul.sharma@example.com", "CSE", "A", 2023),
    ("STU102", "Priya Singh", "priya.singh@example.com", "CSE", "A", 2023),
    ("STU103", "Amit Kumar", "amit.kumar@example.com", "CSE", "B", 2023),
    ("STU104", "Neha Verma", "neha.verma@example.com", "IT", "A", 2023),
    ("STU105", "Arjun Mehta", "arjun.mehta@example.com", "IT", "B", 2023),
    ("STU106", "Simran Kaur", "simran.kaur@example.com", "ECE", "A", 2023),
    ("STU107", "Rohan Gupta", "rohan.gupta@example.com", "ECE", "B", 2023),
    ("STU108", "Ananya Roy", "ananya.roy@example.com", "CSE", "A", 2023),
    ("STU109", "Vikram Yadav", "vikram.yadav@example.com", "ME", "A", 2023),
    ("STU110", "Sneha Patel", "sneha.patel@example.com", "CSE", "B", 2023),
    ("STU111", "Karan Malhotra", "karan.malhotra@example.com", "IT", "A", 2023),
    ("STU112", "Isha Gupta", "isha.gupta@example.com", "CSE", "A", 2023),
    ("STU113", "Aditya Joshi", "aditya.joshi@example.com", "ECE", "A", 2023),
    ("STU114", "Meera Nair", "meera.nair@example.com", "IT", "B", 2023),
    ("STU115", "Dev Kapoor", "dev.kapoor@example.com", "ME", "A", 2023),
    ("STU116", "Pooja Mishra", "pooja.mishra@example.com", "CSE", "B", 2023),
    ("STU117", "Nikhil Jain", "nikhil.jain@example.com", "ECE", "B", 2023),
    ("STU118", "Riya Das", "riya.das@example.com", "IT", "A", 2023),
    ("STU119", "Sahil Khan", "sahil.khan@example.com", "CSE", "A", 2023),
    ("STU120", "Tanya Bansal", "tanya.bansal@example.com", "CSE", "B", 2023),
]


SUBJECT_DATA = [
    # Semester 4
    ("CS401", "Database Management Systems", 4, 100, 4.0),
    ("CS402", "Operating Systems", 4, 100, 4.0),
    ("CS403", "Artificial Intelligence", 4, 100, 4.0),
    ("CS404", "Computer Networks", 4, 100, 4.0),
    ("CS405", "Software Engineering", 4, 100, 3.0),

    # Semester 5
    ("CS501", "Machine Learning", 5, 100, 4.0),
    ("CS502", "Web Technologies", 5, 100, 4.0),
    ("CS503", "Compiler Design", 5, 100, 4.0),
    ("CS504", "Data Analytics", 5, 100, 4.0),
    ("CS505", "Cloud Computing", 5, 100, 3.0),
]


def calculate_grade(total_marks: float) -> tuple[str, float]:
    """Return a letter grade and grade point for a mark."""

    if total_marks >= 90:
        return "A+", 10.0
    if total_marks >= 80:
        return "A", 9.0
    if total_marks >= 70:
        return "B+", 8.0
    if total_marks >= 60:
        return "B", 7.0
    if total_marks >= 50:
        return "C", 6.0
    if total_marks >= 40:
        return "D", 5.0

    return "F", 0.0


def determine_fee_status(
    total_fee: int,
    amount_paid: int,
    due_date: date,
) -> FeeStatus:
    """Derive fee status from the payment and due-date information."""

    if amount_paid >= total_fee:
        return FeeStatus.PAID

    if due_date < date.today():
        return FeeStatus.OVERDUE

    if amount_paid > 0:
        return FeeStatus.PARTIALLY_PAID

    return FeeStatus.PENDING


def clear_existing_data() -> None:
    """
    Remove existing development data.

    Child tables are cleared before their parent tables to avoid
    foreign-key relationship problems.
    """

    with SessionLocal() as db:
        db.execute(delete(Attendance))
        db.execute(delete(Fee))
        db.execute(delete(Mark))
        db.execute(delete(Subject))
        db.execute(delete(Student))
        db.commit()


def create_students() -> list[Student]:
    """Create fictional student ORM objects."""

    students: list[Student] = []

    for student_id, name, email, branch, section, admission_year in STUDENT_DATA:
        students.append(
            Student(
                student_id=student_id,
                name=name,
                email=email,
                branch=branch,
                current_semester=5,
                section=section,
                admission_year=admission_year,
            )
        )

    return students


def create_subjects() -> list[Subject]:
    """Create fictional subject ORM objects."""

    subjects: list[Subject] = []

    for code, name, semester, maximum_marks, credit in SUBJECT_DATA:
        subjects.append(
            Subject(
                subject_code=code,
                subject_name=name,
                semester=semester,
                maximum_marks=maximum_marks,
                credit=credit,
            )
        )

    return subjects


def create_marks(
    students: list[Student],
    subjects: list[Subject],
) -> list[Mark]:
    """Generate deterministic fictional marks for every student."""

    marks: list[Mark] = []

    for student_index, student in enumerate(students):
        for subject_index, subject in enumerate(subjects):
            # Create realistic variation while keeping the dataset reproducible.
            base_score = 52 + ((student_index * 7 + subject_index * 5) % 43)

            internal_marks = round(base_score * 0.30, 1)
            external_marks = round(base_score - internal_marks, 1)
            total_marks = round(internal_marks + external_marks, 1)

            grade, grade_point = calculate_grade(total_marks)

            marks.append(
                Mark(
                    student=student,
                    subject=subject,
                    semester=subject.semester,
                    internal_marks=internal_marks,
                    external_marks=external_marks,
                    total_marks=total_marks,
                    grade=grade,
                    grade_point=grade_point,
                    exam_type="END_SEMESTER",
                    academic_year=ACADEMIC_YEAR,
                )
            )

    return marks


def create_attendance(
    students: list[Student],
    subjects: list[Subject],
) -> list[Attendance]:
    """Generate subject-level attendance records."""

    attendance_records: list[Attendance] = []

    for student_index, student in enumerate(students):
        for subject_index, subject in enumerate(subjects):
            classes_held = 60

            # Produces percentages between roughly 60% and 98%.
            classes_attended = 36 + (
                (student_index * 3 + subject_index * 4) % 24
            )

            attendance_percentage = round(
                (classes_attended / classes_held) * 100,
                2,
            )

            attendance_records.append(
                Attendance(
                    student=student,
                    subject=subject,
                    semester=subject.semester,
                    classes_held=classes_held,
                    classes_attended=classes_attended,
                    attendance_percentage=attendance_percentage,
                    academic_year=ACADEMIC_YEAR,
                )
            )

    return attendance_records


def create_fees(students: list[Student]) -> list[Fee]:
    """Generate semester fee records with varied payment statuses."""

    fees: list[Fee] = []

    # Values are stored in paise.
    total_fee = 5_000_000  # ₹50,000

    payment_patterns = [
        5_000_000,  # Paid
        3_000_000,  # Partially paid
        0,          # Pending
        4_000_000,  # Partially paid
    ]

    for index, student in enumerate(students):
        amount_paid = payment_patterns[index % len(payment_patterns)]

        # Some unpaid records deliberately receive an expired due date.
        if index % 5 == 0:
            due_date = date.today() - timedelta(days=30)
        else:
            due_date = date.today() + timedelta(days=30)

        amount_due = total_fee - amount_paid
        status = determine_fee_status(total_fee, amount_paid, due_date)

        payment_date = (
            date.today() - timedelta(days=10)
            if amount_paid > 0
            else None
        )

        fees.append(
            Fee(
                student=student,
                semester=5,
                total_fee=total_fee,
                amount_paid=amount_paid,
                amount_due=amount_due,
                status=status,
                due_date=due_date,
                payment_date=payment_date,
                academic_year=ACADEMIC_YEAR,
            )
        )

    return fees


def seed_database() -> None:
    """Create tables, reset existing sample data, and insert fresh records."""

    random.seed(RANDOM_SEED)

    create_database_tables()
    clear_existing_data()

    students = create_students()
    subjects = create_subjects()

    marks = create_marks(students, subjects)
    attendance_records = create_attendance(students, subjects)
    fees = create_fees(students)

    with SessionLocal() as db:
        db.add_all(students)
        db.add_all(subjects)
        db.add_all(marks)
        db.add_all(attendance_records)
        db.add_all(fees)

        db.commit()

    print("Database seeded successfully.")
    print(f"Students inserted: {len(students)}")
    print(f"Subjects inserted: {len(subjects)}")
    print(f"Marks inserted: {len(marks)}")
    print(f"Attendance records inserted: {len(attendance_records)}")
    print(f"Fee records inserted: {len(fees)}")


def verify_seeded_data() -> None:
    """Print record counts after seeding."""

    with SessionLocal() as db:
        student_count = len(db.scalars(select(Student)).all())
        subject_count = len(db.scalars(select(Subject)).all())
        mark_count = len(db.scalars(select(Mark)).all())
        attendance_count = len(db.scalars(select(Attendance)).all())
        fee_count = len(db.scalars(select(Fee)).all())

    print("\nVerification")
    print("------------------------------")
    print(f"Students: {student_count}")
    print(f"Subjects: {subject_count}")
    print(f"Marks: {mark_count}")
    print(f"Attendance records: {attendance_count}")
    print(f"Fee records: {fee_count}")


if __name__ == "__main__":
    seed_database()
    verify_seeded_data()