"""Test fixtures and configuration."""

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from src.database import Base
from src.models.user import Invite, User


@pytest_asyncio.fixture
async def session_factory(tmp_path):
    """Async session factory backed by an isolated temp SQLite database."""
    engine: AsyncEngine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/auth_test.db")
    async with engine.begin() as conn:
        auth_tables = [User.__table__, Invite.__table__]
        await conn.run_sync(
            lambda sync_conn: Base.metadata.create_all(sync_conn, tables=auth_tables)
        )
    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory
    await engine.dispose()
