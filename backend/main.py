"""Main FastAPI application."""

from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from backend.api.analytics import router as analytics_router
from backend.api.query import router as query_router
from backend.api.students import router as students_router
from backend.api.uploads import router as uploads_router
from backend.config import settings
from backend.core.exception_handlers import register_exception_handlers
from backend.database import SessionLocal, create_database_tables


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Run application startup and shutdown operations."""

    create_database_tables()
    yield


app = FastAPI(
    title=settings.app_name,
    description=(
        "Backend API for querying structured school data using "
        "FastAPI, SQLAlchemy, and a safe LLM-based intent interpreter."
    ),
    version="0.1.0",
    debug=settings.debug,
    lifespan=lifespan,
)


register_exception_handlers(app)

app.include_router(students_router)
app.include_router(analytics_router)
app.include_router(uploads_router)
app.include_router(query_router)


@app.get("/", tags=["General"])
def root() -> dict[str, str]:
    """Return basic information about the API."""

    return {
        "message": "School Database LLM Chatbot API",
        "docs": "/docs",
    }


@app.get("/api/v1/health", tags=["Health"])
def health_check() -> dict[str, Any]:
    """Check whether the API, database, and LLM are configured."""

    llm_status = (
        "configured"
        if settings.llm_enabled
        and settings.azure_openai_configured
        else "not_configured"
    )

    try:
        with SessionLocal() as database:
            database.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "connected",
            "llm": llm_status,
            "version": "0.1.0",
        }

    except SQLAlchemyError:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "llm": llm_status,
            "version": "0.1.0",
        }