"""Populate the development database with fictional school records."""

from __future__ import annotations

import random
from datetime import date, timedelta

from sqlalchemy import delete, select

from backend.database import SessionLocal, create_database_tables
from backend.models import (
    Attendance,
    Fee,
    FeeStatus,
    Mark,
    Student,
    Subject,
)


ACADEMIC_YEAR = "2025-2026"
RANDOM_SEED = 42
TOTAL_STUDENTS = 120


FIRST_NAMES = [
    "Aarav",
    "Aditi",
    "Aditya",
    "Akash",
    "Aman",
    "Ananya",
    "Anjali",
    "Ankit",
    "Arjun",
    "Aryan",
    "Ayush",
    "Dev",
    "Diya",
    "Harsh",
    "Isha",
    "Kabir",
    "Karan",
    "Kavya",
    "Khushi",
    "Manav",
    "Meera",
    "Mohit",
    "Muskan",
    "Neha",
    "Nikhil",
    "Pooja",
    "Pranav",
    "Priya",
    "Rahul",
    "Riya",
    "Rohan",
    "Sahil",
    "Sakshi",
    "Samarth",
    "Simran",
    "Sneha",
    "Tanvi",
    "Varun",
    "Vikram",
    "Yash",
]

LAST_NAMES = [
    "Agarwal",
    "Arora",
    "Bansal",
    "Chauhan",
    "Das",
    "Gupta",
    "Jain",
    "Joshi",
    "Kapoor",
    "Kaur",
    "Khan",
    "Kumar",
    "Malhotra",
    "Mehta",
    "Mishra",
    "Nair",
    "Pandey",
    "Patel",
    "Rajput",
    "Rana",
    "Roy",
    "Saini",
    "Saxena",
    "Sharma",
    "Singh",
    "Thakur",
    "Verma",
    "Yadav",
]

BRANCHES = [
    "CSE",
    "IT",
    "ECE",
    "ME",
]

SECTIONS = [
    "A",
    "B",
]


SUBJECT_DATA = [
    # Semester 2
    ("CS201", "Data Structures", 2, 100, 4.0),
    ("CS202", "Object Oriented Programming", 2, 100, 4.0),
    ("CS203", "Discrete Mathematics", 2, 100, 3.0),
    ("CS204", "Computer Organization", 2, 100, 4.0),
    ("CS205", "Environmental Studies", 2, 100, 2.0),

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
    """Derive fee status from payment and due-date information."""

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

    Child tables are cleared before parent tables to avoid
    foreign-key relationship problems.
    """

    with SessionLocal() as db:
        db.execute(delete(Attendance))
        db.execute(delete(Fee))
        db.execute(delete(Mark))
        db.execute(delete(Subject))
        db.execute(delete(Student))
        db.commit()


def generate_student_name(index: int) -> str:
    """Generate a deterministic fictional student name."""

    first_name = FIRST_NAMES[index % len(FIRST_NAMES)]

    last_name_index = (
        index // len(FIRST_NAMES) + index
    ) % len(LAST_NAMES)

    last_name = LAST_NAMES[last_name_index]

    return f"{first_name} {last_name}"


def generate_student_email(
    name: str,
    student_id: str,
) -> str:
    """Generate a unique fictional email address."""

    normalized_name = (
        name.lower()
        .replace(" ", ".")
        .replace("'", "")
    )

    return f"{normalized_name}.{student_id.lower()}@example.com"


def create_students() -> list[Student]:
    """Create 120 fictional student ORM objects."""

    students: list[Student] = []

    for index in range(TOTAL_STUDENTS):
        numeric_id = 101 + index
        student_id = f"STU{numeric_id}"

        name = generate_student_name(index)
        email = generate_student_email(name, student_id)

        branch = BRANCHES[index % len(BRANCHES)]
        section = SECTIONS[index % len(SECTIONS)]

        # Most students are currently in semesters 4 or 5.
        current_semester = 4 if index % 3 == 0 else 5

        admission_year = (
            2024
            if current_semester == 4
            else 2023
        )

        students.append(
            Student(
                student_id=student_id,
                name=name,
                email=email,
                branch=branch,
                current_semester=current_semester,
                section=section,
                admission_year=admission_year,
            )
        )

    return students


def create_subjects() -> list[Subject]:
    """Create fictional subject ORM objects."""

    subjects: list[Subject] = []

    for (
        code,
        name,
        semester,
        maximum_marks,
        credit,
    ) in SUBJECT_DATA:
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
    """Generate deterministic marks for every student and subject."""

    marks: list[Mark] = []

    for student_index, student in enumerate(students):
        for subject_index, subject in enumerate(subjects):
            score_variation = (
                student_index * 7
                + subject_index * 5
                + subject.semester * 3
            ) % 51

            total_marks = 45 + score_variation

            internal_marks = round(
                total_marks * 0.30,
                1,
            )

            external_marks = round(
                total_marks - internal_marks,
                1,
            )

            total_marks = round(
                internal_marks + external_marks,
                1,
            )

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

            classes_attended = 34 + (
                student_index * 3
                + subject_index * 4
            ) % 26

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
    total_fee = 7_500_000  # ₹75,000

    payment_patterns = [
        7_500_000,  # Paid
        4_500_000,  # Partially paid
        3_000_000,  # Partially paid
        0,          # Pending or overdue
    ]

    for index, student in enumerate(students):
        amount_paid = payment_patterns[
            index % len(payment_patterns)
        ]

        if index % 6 == 0:
            due_date = date.today() - timedelta(days=30)
        else:
            due_date = date.today() + timedelta(days=30)

        amount_due = total_fee - amount_paid

        status = determine_fee_status(
            total_fee=total_fee,
            amount_paid=amount_paid,
            due_date=due_date,
        )

        payment_date = (
            date.today() - timedelta(days=10)
            if amount_paid > 0
            else None
        )

        fees.append(
            Fee(
                student=student,
                semester=student.current_semester,
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
    """Reset the development database and insert fictional records."""

    random.seed(RANDOM_SEED)

    create_database_tables()
    clear_existing_data()

    students = create_students()
    subjects = create_subjects()

    marks = create_marks(
        students=students,
        subjects=subjects,
    )

    attendance_records = create_attendance(
        students=students,
        subjects=subjects,
    )

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
    print(
        "Attendance records inserted: "
        f"{len(attendance_records)}"
    )
    print(f"Fee records inserted: {len(fees)}")


def verify_seeded_data() -> None:
    """Print record counts after seeding."""

    with SessionLocal() as db:
        student_count = len(
            db.scalars(select(Student)).all()
        )

        subject_count = len(
            db.scalars(select(Subject)).all()
        )

        mark_count = len(
            db.scalars(select(Mark)).all()
        )

        attendance_count = len(
            db.scalars(select(Attendance)).all()
        )

        fee_count = len(
            db.scalars(select(Fee)).all()
        )

    print("\nVerification")
    print("------------------------------")
    print(f"Students: {student_count}")
    print(f"Subjects: {subject_count}")
    print(f"Marks: {mark_count}")
    print(
        "Attendance records: "
        f"{attendance_count}"
    )
    print(f"Fee records: {fee_count}")


if __name__ == "__main__":
    seed_database()
    verify_seeded_data()