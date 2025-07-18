"""
SQLAlchemy Core database configuration and connection management.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncConnection, async_sessionmaker
from typing import AsyncGenerator
from dotenv import load_dotenv

from .tables import metadata

# Load environment variables
load_dotenv()

# Database URL - using environment variable or default for development
DATABASE_URL = os.getenv(
    "DATABASE_URL_ASYNC", 
    "postgresql+asyncpg://postgres:postgres@localhost:5432/chatbot_db"
)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Set to False in production
    future=True
)

# Create async session factory (still useful for transactions)
async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncConnection, None]:
    """Get database connection for Core operations"""
    async with engine.begin() as conn:
        yield conn


async def get_async_connection() -> AsyncConnection:
    """Get async connection for direct use in services"""
    return await engine.connect()


# async def create_tables():
#     """Create all tables using Core metadata"""
#     async with engine.begin() as conn:
#         await conn.run_sync(metadata.create_all)


# async def drop_tables():
#     """Drop all tables using Core metadata"""
#     async with engine.begin() as conn:
#         await conn.run_sync(metadata.drop_all)


# Export the engine and metadata for direct use
__all__ = [
    "engine",
    "metadata", 
    "get_db",
    "get_async_connection",
    # "create_tables",
    # "drop_tables"
]