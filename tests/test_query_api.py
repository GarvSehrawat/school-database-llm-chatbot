"""Tests for the natural-language query API."""

from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_health_endpoint() -> None:
    """Confirm the backend health endpoint is available."""

    response = client.get("/api/v1/health")

    assert response.status_code == 200


def test_marks_query_endpoint() -> None:
    """Return marks for a valid student and semester query."""

    response = client.post(
        "/api/v1/query",
        json={
            "query": "Show semester 2 marks of STU121",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["parsed_query"]["intent"] == "get_marks"
    assert body["parsed_query"]["student_id"] == "STU121"
    assert body["parsed_query"]["semester"] == 2
    assert isinstance(body["data"], list)
    assert len(body["data"]) >= 1
    assert body["data"][0]["subject_code"] == "CS201"


def test_top_students_query_endpoint() -> None:
    """Return ranked students for a semester."""

    response = client.post(
        "/api/v1/query",
        json={
            "query": "Show top 5 students in semester 2",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["parsed_query"]["intent"] == "get_top_students"
    assert body["parsed_query"]["semester"] == 2
    assert body["parsed_query"]["limit"] == 5
    assert isinstance(body["data"], list)


def test_unknown_query_endpoint() -> None:
    """Return a safe UNKNOWN response for unsupported questions."""

    response = client.post(
        "/api/v1/query",
        json={
            "query": "Tell me a joke",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["parsed_query"]["intent"] == "unknown"
    assert body["data"] is None


def test_marks_query_without_student_id() -> None:
    """Reject a marks query that does not include a student ID."""

    response = client.post(
        "/api/v1/query",
        json={
            "query": "Show marks",
        },
    )

    assert response.status_code == 400


def test_query_request_body_validation() -> None:
    """Reject an empty natural-language query."""

    response = client.post(
        "/api/v1/query",
        json={
            "query": "",
        },
    )

    assert response.status_code == 422