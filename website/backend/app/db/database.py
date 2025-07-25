import os
import urllib.parse
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base
from app.core.centralized_logging import get_logger

logger = get_logger()


def build_database_url() -> str | None:
    """Build the database URL from environment variables with proper encoding."""
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    name = os.getenv("DB_NAME")

    if not all([user, password, host, port, name]):
        return None

    encoded_password = urllib.parse.quote_plus(password) if password else ""
    return f"mysql+asyncmy://{user}:{encoded_password}@{host}:{port}/{name}"


def get_engine(database_url: str | None = None, echo: bool = True) -> AsyncEngine:
    """Lazily create and return an async SQLAlchemy engine."""
    url = database_url or build_database_url()
    if not url:
        raise RuntimeError("DATABASE_URL is not set or incomplete")
    engine = create_async_engine(url, echo=echo)
    logger.debug(f"[ENGINE] Created AsyncEngine {id(engine)} with url: {url}")
    return engine


def get_session_maker(
    engine: AsyncEngine | None = None,
) -> async_sessionmaker[AsyncSession]:
    """Return an async sessionmaker bound to the given engine."""
    if engine is None:
        engine = get_engine()
    session_maker = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
    logger.debug(
        f"[SESSIONMAKER] Created async_sessionmaker {id(session_maker)} bound to engine {id(engine)}"
    )
    return session_maker


# Async session generator (for FastAPI dependency injection)
async def get_db() -> AsyncGenerator[AsyncSession]:
    """Yield an async database session for dependency injection."""
    engine = get_engine()
    session_local = get_session_maker(engine)
    async with session_local() as session:
        logger.debug(f"[SESSION] get_db: Yielding session {id(session)} from generator")
        yield session
        logger.debug(f"[SESSION] get_db: Session {id(session)} closed after yield")


# Base class for models
Base = declarative_base()
