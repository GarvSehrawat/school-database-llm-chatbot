"""Streamlit frontend for the School Database LLM Chatbot."""

from __future__ import annotations

from typing import Any

import requests
import streamlit as st


API_BASE_URL = "http://127.0.0.1:8000"

QUERY_ENDPOINT = f"{API_BASE_URL}/api/v1/query"
HEALTH_ENDPOINT = f"{API_BASE_URL}/api/v1/health"

UPLOAD_ENDPOINTS = {
    "Students": f"{API_BASE_URL}/api/v1/uploads/students",
    "Subjects": f"{API_BASE_URL}/api/v1/uploads/subjects",
    "Marks": f"{API_BASE_URL}/api/v1/uploads/marks",
    "Attendance": f"{API_BASE_URL}/api/v1/uploads/attendance",
    "Fees": f"{API_BASE_URL}/api/v1/uploads/fees",
}


st.set_page_config(
    page_title="School Database Chatbot",
    page_icon="🎓",
    layout="wide",
)


def check_backend_health() -> bool:
    """Return whether the FastAPI backend is reachable."""

    try:
        response = requests.get(
            HEALTH_ENDPOINT,
            timeout=5,
        )

        return response.status_code == 200

    except requests.RequestException:
        return False


def send_query(query: str) -> dict[str, Any]:
    """Send a natural-language question to the FastAPI backend."""

    response = requests.post(
        QUERY_ENDPOINT,
        json={"query": query},
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


def upload_csv_file(
    file_type: str,
    uploaded_file: Any,
    replace_existing: bool,
) -> dict[str, Any]:
    """Upload a CSV file to the selected FastAPI endpoint."""

    endpoint = UPLOAD_ENDPOINTS[file_type]

    files = {
        "file": (
            uploaded_file.name,
            uploaded_file.getvalue(),
            "text/csv",
        )
    }

    data = {
        "replace_existing": str(replace_existing).lower(),
    }

    response = requests.post(
        endpoint,
        files=files,
        data=data,
        timeout=60,
    )

    response.raise_for_status()

    return response.json()


def initialize_chat_history() -> None:
    """Create the Streamlit chat history if it does not exist."""

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "Hello! Ask me about student profiles, marks, "
                    "attendance, fees, ranks, toppers, or school analytics."
                ),
                "data": None,
            }
        ]


def render_query_data(data: Any) -> None:
    """Display structured query data in a readable format."""

    if not data:
        return

    if isinstance(data, list):
        if all(isinstance(item, dict) for item in data):
            st.dataframe(
                data,
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.json(data)

        return

    if isinstance(data, dict):
        st.json(data)
        return

    st.write(data)


def display_chat_history() -> None:
    """Display saved chat messages and their structured result data."""

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            message_data = message.get("data")

            if message_data:
                render_query_data(message_data)


def extract_http_error_message(
    exc: requests.HTTPError,
    fallback_message: str,
) -> str:
    """Extract a readable FastAPI error response."""

    if exc.response is None:
        return fallback_message

    try:
        error_data = exc.response.json()
    except ValueError:
        return fallback_message

    detail = error_data.get("detail")

    if isinstance(detail, str):
        return detail

    if isinstance(detail, list):
        messages: list[str] = []

        for item in detail:
            if isinstance(item, dict):
                message = item.get("msg")

                if message:
                    messages.append(str(message))

        if messages:
            return "; ".join(messages)

    error = error_data.get("error")

    if isinstance(error, dict):
        message = error.get("message")

        if message:
            return str(message)

    return fallback_message


def render_upload_summary(result: dict[str, Any]) -> None:
    """Display the CSV import summary returned by FastAPI."""

    total_rows = result.get("total_rows", 0)
    inserted_rows = result.get("inserted_rows", 0)
    updated_rows = result.get("updated_rows", 0)
    skipped_rows = result.get("skipped_rows", 0)
    failed_rows = result.get("failed_rows", 0)

    st.caption(f"Total CSV rows processed: {total_rows}")

    first_column, second_column = st.columns(2)

    with first_column:
        st.metric(
            "Inserted",
            inserted_rows,
        )
        st.metric(
            "Skipped",
            skipped_rows,
        )

    with second_column:
        st.metric(
            "Updated",
            updated_rows,
        )
        st.metric(
            "Failed",
            failed_rows,
        )

    errors = result.get("errors", [])

    if errors:
        st.warning("Some CSV rows could not be imported.")

        st.dataframe(
            errors,
            use_container_width=True,
            hide_index=True,
        )


def render_upload_sidebar(backend_online: bool) -> None:
    """Render CSV upload controls in the Streamlit sidebar."""

    with st.sidebar:
        st.header("📁 CSV Data Upload")

        st.caption(
            "Upload school data directly into the backend database."
        )

        if backend_online:
            st.success(
                "Backend available",
                icon="✅",
            )
        else:
            st.error(
                "Backend unavailable",
                icon="⚠️",
            )

        file_type = st.selectbox(
            "Choose data type",
            options=list(UPLOAD_ENDPOINTS.keys()),
        )

        uploaded_file = st.file_uploader(
            f"Upload {file_type.lower()} CSV",
            type=["csv"],
            key=f"{file_type.lower()}_csv_uploader",
        )

        replace_existing = st.checkbox(
            "Replace existing records",
            value=False,
            help=(
                "When enabled, records with matching identifiers "
                "will be updated."
            ),
        )

        upload_clicked = st.button(
            "Upload CSV",
            type="primary",
            use_container_width=True,
            disabled=not backend_online,
        )

        if not backend_online:
            st.info(
                "Start FastAPI before using CSV uploads."
            )

            return

        if not upload_clicked:
            return

        if uploaded_file is None:
            st.warning("Choose a CSV file before uploading.")
            return

        try:
            with st.spinner("Uploading and validating CSV..."):
                result = upload_csv_file(
                    file_type=file_type,
                    uploaded_file=uploaded_file,
                    replace_existing=replace_existing,
                )

            st.success(
                f"{file_type} CSV processed successfully."
            )

            render_upload_summary(result)

        except requests.HTTPError as exc:
            st.error(
                extract_http_error_message(
                    exc=exc,
                    fallback_message="The CSV upload failed.",
                )
            )

        except requests.Timeout:
            st.error(
                "The CSV upload timed out. Try again with a smaller file."
            )

        except requests.RequestException:
            st.error(
                "The backend connection failed during upload."
            )


def render_backend_status(backend_online: bool) -> None:
    """Display the FastAPI connection status."""

    if backend_online:
        st.success(
            "Backend connected",
            icon="✅",
        )
    else:
        st.error(
            "FastAPI backend is not running. Start it using: "
            "`uvicorn backend.main:app --reload`",
            icon="⚠️",
        )


def save_assistant_message(
    content: str,
    data: Any = None,
) -> None:
    """Save an assistant response and optional structured data."""

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": content,
            "data": data,
        }
    )


def render_chat_response(
    user_query: str,
    backend_online: bool,
) -> None:
    """Send the user question and render the assistant response."""

    with st.chat_message("assistant"):
        if not backend_online:
            error_message = (
                "I cannot reach the backend right now. Start FastAPI "
                "and then try again."
            )

            st.error(error_message)

            save_assistant_message(error_message)

            return

        try:
            with st.spinner("Searching school records..."):
                result = send_query(user_query)

            answer = result.get(
                "message",
                "The backend returned no readable answer.",
            )

            result_data = result.get("data")

            st.markdown(answer)

            render_query_data(result_data)

            save_assistant_message(
                content=answer,
                data=result_data,
            )

        except requests.HTTPError as exc:
            error_message = extract_http_error_message(
                exc=exc,
                fallback_message="The request could not be completed.",
            )

            st.error(error_message)

            save_assistant_message(error_message)

        except requests.Timeout:
            error_message = (
                "The request timed out. Please try again."
            )

            st.error(error_message)

            save_assistant_message(error_message)

        except requests.RequestException:
            error_message = (
                "The backend connection failed. Check that FastAPI "
                "is running on port 8000."
            )

            st.error(error_message)

            save_assistant_message(error_message)


def main() -> None:
    """Render the main Streamlit application."""

    initialize_chat_history()

    backend_online = check_backend_health()

    render_upload_sidebar(backend_online)

    st.title("🎓 School Database LLM Chatbot")

    st.caption(
        "Ask questions about students, marks, attendance, fees, "
        "rankings, and analytics."
    )

    render_backend_status(backend_online)

    st.divider()

    display_chat_history()

    user_query = st.chat_input(
        "Example: Show semester 2 marks of STU121"
    )

    if not user_query:
        return

    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_query,
            "data": None,
        }
    )

    with st.chat_message("user"):
        st.markdown(user_query)

    render_chat_response(
        user_query=user_query,
        backend_online=backend_online,
    )


if __name__ == "__main__":
    main()