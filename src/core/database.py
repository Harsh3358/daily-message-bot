"""Async database engine and session configuration.

Async Concepts in SQLAlchemy 2.x:
1. `create_async_engine`: Manages an asynchronous connection pool using `asyncpg`.
   Unlike synchronous drivers (like psycopg2), `asyncpg` does not block the Python
   thread while waiting for query responses from PostgreSQL.
2. `async_sessionmaker`: Factory for creating `AsyncSession` instances.
3. `AsyncSession`: An asynchronous handle for executing queries (`await session.execute(...)`)
   and managing transactions (`await session.commit()`, `await session.rollback()`).
   `expire_on_commit=False` ensures attributes remain accessible after commit without
   triggering synchronous lazy loads.
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from src.core.config import get_settings

settings = get_settings()

# Create async engine with connection pooling
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
)

# Async session factory
async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an asynchronous SQLAlchemy session.

    Ensures the session is cleanly closed when the request lifecycle ends.
    """
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
