"""Tests for CSV upload API endpoints."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.database import Base, get_db
from backend.main import app

# Import models so their tables are registered with Base.metadata.
from backend.models.attendance import Attendance  # noqa: F401
from backend.models.fee import Fee  # noqa: F401
from backend.models.mark import Mark  # noqa: F401
from backend.models.student import Student  # noqa: F401
from backend.models.subject import Subject  # noqa: F401


@pytest.fixture
def client(tmp_path) -> Generator[TestClient, None, None]:
    """Provide a TestClient connected to an isolated temporary database."""

    database_path = tmp_path / "test_school.db"

    engine = create_engine(
        f"sqlite:///{database_path}",
        connect_args={
            "check_same_thread": False,
        },
    )

    testing_session_factory = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        class_=Session,
    )

    Base.metadata.create_all(bind=engine)

    def override_get_db() -> Generator[Session, None, None]:
        database = testing_session_factory()

        try:
            yield database
        finally:
            database.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def student_csv(
    *,
    name: str = "Test Student",
    semester: int = 2,
) -> bytes:
    """Create valid student CSV content."""

    content = (
        "student_id,name,email,branch,current_semester,"
        "section,admission_year\n"
        f"TEST001,{name},test001@example.com,CSE,"
        f"{semester},A,2025\n"
    )

    return content.encode("utf-8")


def test_upload_new_student_csv(client: TestClient) -> None:
    """Insert a new student from a valid CSV file."""

    response = client.post(
        "/api/v1/uploads/students",
        files={
            "file": (
                "students.csv",
                student_csv(),
                "text/csv",
            )
        },
        data={
            "replace_existing": "false",
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["file_type"] == "students"
    assert body["total_rows"] == 1
    assert body["inserted_rows"] == 1
    assert body["updated_rows"] == 0
    assert body["skipped_rows"] == 0
    assert body["failed_rows"] == 0
    assert body["errors"] == []


def test_duplicate_student_is_skipped(client: TestClient) -> None:
    """Skip an existing student when replacement is disabled."""

    first_response = client.post(
        "/api/v1/uploads/students",
        files={
            "file": (
                "students.csv",
                student_csv(),
                "text/csv",
            )
        },
        data={
            "replace_existing": "false",
        },
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/api/v1/uploads/students",
        files={
            "file": (
                "students.csv",
                student_csv(),
                "text/csv",
            )
        },
        data={
            "replace_existing": "false",
        },
    )

    assert second_response.status_code == 201

    body = second_response.json()

    assert body["inserted_rows"] == 0
    assert body["updated_rows"] == 0
    assert body["skipped_rows"] == 1
    assert body["failed_rows"] == 0


def test_existing_student_is_updated(client: TestClient) -> None:
    """Update an existing student when replacement is enabled."""

    first_response = client.post(
        "/api/v1/uploads/students",
        files={
            "file": (
                "students.csv",
                student_csv(),
                "text/csv",
            )
        },
        data={
            "replace_existing": "false",
        },
    )

    assert first_response.status_code == 201

    update_response = client.post(
        "/api/v1/uploads/students",
        files={
            "file": (
                "students.csv",
                student_csv(
                    name="Updated Student",
                    semester=3,
                ),
                "text/csv",
            )
        },
        data={
            "replace_existing": "true",
        },
    )

    assert update_response.status_code == 201

    body = update_response.json()

    assert body["inserted_rows"] == 0
    assert body["updated_rows"] == 1
    assert body["skipped_rows"] == 0
    assert body["failed_rows"] == 0

    student_response = client.get(
        "/api/v1/students/TEST001"
    )

    assert student_response.status_code == 200

    student = student_response.json()

    assert student["name"] == "Updated Student"
    assert student["current_semester"] == 3


def test_student_csv_with_missing_columns(
    client: TestClient,
) -> None:
    """Reject a CSV that does not contain required columns."""

    invalid_csv = (
        "student_id,name\n"
        "TEST001,Test Student\n"
    ).encode("utf-8")

    response = client.post(
        "/api/v1/uploads/students",
        files={
            "file": (
                "students.csv",
                invalid_csv,
                "text/csv",
            )
        },
        data={
            "replace_existing": "false",
        },
    )

    assert response.status_code == 400

    body = response.json()

    assert "Missing required CSV columns" in body["detail"]


def test_student_csv_with_invalid_row(
    client: TestClient,
) -> None:
    """Return a row-level failure for invalid student data."""

    invalid_csv = (
        "student_id,name,email,branch,current_semester,"
        "section,admission_year\n"
        "TEST001,Test Student,test001@example.com,CSE,"
        "12,A,2025\n"
    ).encode("utf-8")

    response = client.post(
        "/api/v1/uploads/students",
        files={
            "file": (
                "students.csv",
                invalid_csv,
                "text/csv",
            )
        },
        data={
            "replace_existing": "false",
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["inserted_rows"] == 0
    assert body["failed_rows"] == 1
    assert len(body["errors"]) == 1
    assert "between 1 and 8" in body["errors"][0]["message"]


def test_reject_non_csv_file(client: TestClient) -> None:
    """Reject an uploaded file that does not have a CSV extension."""

    response = client.post(
        "/api/v1/uploads/students",
        files={
            "file": (
                "students.txt",
                student_csv(),
                "text/plain",
            )
        },
        data={
            "replace_existing": "false",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Only CSV files are supported."