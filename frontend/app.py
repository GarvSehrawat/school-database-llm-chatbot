"""Streamlit frontend for the School Database LLM Chatbot."""

from __future__ import annotations

import requests
import streamlit as st


API_BASE_URL = "http://127.0.0.1:8000"
QUERY_ENDPOINT = f"{API_BASE_URL}/api/v1/query"
HEALTH_ENDPOINT = f"{API_BASE_URL}/api/v1/health"


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


def send_query(query: str) -> dict:
    """Send a natural-language question to the FastAPI backend."""

    response = requests.post(
        QUERY_ENDPOINT,
        json={"query": query},
        timeout=30,
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
            }
        ]


def display_chat_history() -> None:
    """Display all saved chat messages."""

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def main() -> None:
    """Render the main Streamlit application."""

    initialize_chat_history()

    st.title("🎓 School Database LLM Chatbot")

    st.caption(
        "Ask questions about students, marks, attendance, fees, "
        "rankings, and analytics."
    )

    backend_online = check_backend_health()

    if backend_online:
        st.success("Backend connected", icon="✅")
    else:
        st.error(
            "FastAPI backend is not running. Start it using: "
            "`uvicorn backend.main:app --reload`",
            icon="⚠️",
        )

    st.divider()

    display_chat_history()

    user_query = st.chat_input(
        "Example: Show semester 2 marks of STU121"
    )

    if user_query:
        st.session_state.messages.append(
            {
                "role": "user",
                "content": user_query,
            }
        )

        with st.chat_message("user"):
            st.markdown(user_query)

        with st.chat_message("assistant"):
            if not backend_online:
                error_message = (
                    "I cannot reach the backend right now. Start FastAPI "
                    "and then try again."
                )

                st.error(error_message)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": error_message,
                    }
                )

                return

            try:
                with st.spinner("Searching school records..."):
                    result = send_query(user_query)

                answer = result.get(
                    "message",
                    "The backend returned no readable answer.",
                )

                st.markdown(answer)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                    }
                )

            except requests.HTTPError as exc:
                error_message = "The request could not be completed."

                if exc.response is not None:
                    try:
                        error_data = exc.response.json()
                        error_message = error_data.get(
                            "detail",
                            error_message,
                        )
                    except ValueError:
                        pass

                st.error(error_message)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": error_message,
                    }
                )

            except requests.RequestException:
                error_message = (
                    "The backend connection failed. Check that FastAPI "
                    "is running on port 8000."
                )

                st.error(error_message)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": error_message,
                    }
                )


if __name__ == "__main__":
    main()