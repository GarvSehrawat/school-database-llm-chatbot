"""SQLAlchemy database engine, sessions, and table initialization."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from backend.config import settings


class Base(DeclarativeBase):
    """Base class inherited by all SQLAlchemy models."""

    pass


def normalize_database_url(database_url: str) -> str:
    """
    Normalize database URLs for SQLAlchemy and psycopg.

    Some hosting platforms provide URLs beginning with ``postgres://``.
    SQLAlchemy expects a PostgreSQL dialect URL, and this project uses
    psycopg version 3.
    """

    normalized_url = database_url.strip()

    if normalized_url.startswith("postgres://"):
        normalized_url = normalized_url.replace(
            "postgres://",
            "postgresql+psycopg://",
            1,
        )

    elif normalized_url.startswith("postgresql://"):
        normalized_url = normalized_url.replace(
            "postgresql://",
            "postgresql+psycopg://",
            1,
        )

    return normalized_url


def create_database_engine() -> Engine:
    """Create the appropriate SQLAlchemy engine for the configured database."""

    database_url = normalize_database_url(
        settings.database_url
    )

    if database_url.startswith("sqlite"):
        return create_engine(
            database_url,
            echo=settings.sql_echo,
            connect_args={
                "check_same_thread": False,
            },
        )

    return create_engine(
        database_url,
        echo=settings.sql_echo,
        pool_pre_ping=True,
        pool_recycle=300,
    )


engine = create_database_engine()


SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """
    Provide a database session to a FastAPI route.

    The session is rolled back if an unexpected database error occurs and is
    always closed after the request finishes.
    """

    database = SessionLocal()

    try:
        yield database

    except Exception:
        database.rollback()
        raise

    finally:
        database.close()


def create_database_tables() -> None:
    """Create all database tables that do not already exist."""

    # Importing models registers them with Base.metadata.
    from backend.models import (  # noqa: F401
        Attendance,
        Fee,
        Mark,
        Student,
        Subject,
    )

    Base.metadata.create_all(bind=engine)