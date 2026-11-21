"""MongoDB database client and collections management using Motor and PyMongo."""

import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings

logger = logging.getLogger(__name__)


class Database:
    """Singleton MongoDB connection manager."""

    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None


db = Database()


async def connect_to_mongo():
    """Connect to MongoDB on application startup."""
    try:
        logger.info(f"Connecting to MongoDB at {settings.MONGODB_URL}...")
        db.client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            serverSelectionTimeoutMS=5000,
        )
        db.db = db.client[settings.DATABASE_NAME]

        # Verify connection
        await db.client.admin.command("ping")
        logger.info(f"Connected to MongoDB database: {settings.DATABASE_NAME}")

        # Create indexes
        await _create_indexes()
    except Exception as exc:
        logger.error(f"Failed to connect to MongoDB: {exc}")
        # Note: We do not crash the app so health checks / offline status can still report cleanly
        pass


async def close_mongo_connection():
    """Close MongoDB connection on application shutdown."""
    if db.client:
        logger.info("Closing MongoDB connection...")
        db.client.close()
        logger.info("MongoDB connection closed.")


async def _create_indexes():
    """Create essential indexes for performance, uniqueness, and recruiter scoping."""
    if db.db is None:
        return

    try:
        # Recruiter indexes: email must be unique
        await db.db.recruiters.create_index("email", unique=True)

        # Job Analysis indexes: recruiter_id, created_at
        await db.db.job_analyses.create_index([("recruiter_id", 1), ("created_at", -1)])

        # Candidate indexes: analysis_id, recruiter_id, candidate_id
        await db.db.candidates.create_index([("analysis_id", 1), ("candidate_id", 1)], unique=True)
        await db.db.candidates.create_index([("recruiter_id", 1), ("analysis_id", 1)])
        await db.db.candidates.create_index([("analysis_id", 1), ("status", 1)])

        logger.info("MongoDB indexes verified and created.")
    except Exception as exc:
        logger.warning(f"Error creating MongoDB indexes: {exc}")


"""MongoDB database client and collections management using Motor and PyMongo."""

import asyncio
import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings

logger = logging.getLogger(__name__)


class Database:
    """Singleton MongoDB connection manager."""

    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None
    loop: Optional[asyncio.AbstractEventLoop] = None


db = Database()


async def connect_to_mongo():
    """Connect to MongoDB on application startup."""
    try:
        current_loop = asyncio.get_running_loop()
        db.loop = current_loop
        db.client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            serverSelectionTimeoutMS=5000,
        )
        db.db = db.client[settings.DATABASE_NAME]

        # Verify connection
        await db.client.admin.command("ping")
        logger.info(f"Connected to MongoDB database: {settings.DATABASE_NAME}")

        # Create indexes
        await _create_indexes()
    except Exception as exc:
        logger.error(f"Failed to connect to MongoDB: {exc}")
        pass


async def close_mongo_connection():
    """Close MongoDB connection on application shutdown."""
    if db.client:
        db.client.close()
        db.client = None
        db.db = None
        db.loop = None
        logger.info("MongoDB connection closed.")


async def _create_indexes():
    """Create essential indexes for performance, uniqueness, and recruiter scoping."""
    if db.db is None:
        return

    try:
        # Recruiter indexes: email must be unique
        await db.db.recruiters.create_index("email", unique=True)

        # Job Analysis indexes: recruiter_id, created_at
        await db.db.job_analyses.create_index([("recruiter_id", 1), ("created_at", -1)])

        # Candidate indexes: analysis_id, recruiter_id, candidate_id
        await db.db.candidates.create_index([("analysis_id", 1), ("candidate_id", 1)], unique=True)
        await db.db.candidates.create_index([("recruiter_id", 1), ("analysis_id", 1)])
        await db.db.candidates.create_index([("analysis_id", 1), ("status", 1)])

        logger.info("MongoDB indexes verified and created.")
    except Exception as exc:
        logger.warning(f"Error creating MongoDB indexes: {exc}")


def get_database() -> Optional[AsyncIOMotorDatabase]:
    """Retrieve database instance, ensuring client is bound to the currently running event loop."""
    try:
        current_loop = asyncio.get_running_loop()
    except RuntimeError:
        current_loop = None

    if db.db is None or db.client is None or (current_loop and db.loop != current_loop):
        try:
            db.client = AsyncIOMotorClient(
                settings.MONGODB_URL,
                serverSelectionTimeoutMS=5000,
            )
            db.db = db.client[settings.DATABASE_NAME]
            db.loop = current_loop
        except Exception as exc:
            logger.error(f"MongoDB connection error: {exc}")
            return None
    return db.db


