from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from backend.config import settings
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
        "FastAPI, SQLAlchemy, and an LLM-based intent interpreter."
    ),
    version="0.1.0",
    debug=settings.debug,
    lifespan=lifespan,
)


@app.get("/", tags=["General"])
def root() -> dict[str, str]:
    """Return basic information about the API."""

    return {
        "message": "School Database LLM Chatbot API",
        "docs": "/docs",
    }


@app.get("/api/v1/health", tags=["Health"])
def health_check() -> dict[str, Any]:
    """Check whether the API and database are available."""

    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "connected",
            "llm": "not_configured",
            "version": "0.1.0",
        }

    except SQLAlchemyError:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "llm": "not_configured",
            "version": "0.1.0",
        }