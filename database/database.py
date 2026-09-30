"""
Database engine, session, and helper functions.
"""
import logging
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import select, update

from config import config
from database.models import Base, User, UserSettings, Download

logger = logging.getLogger(__name__)

engine = create_async_engine(config.DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    """Create all tables if they don't exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized: %s", config.DATABASE_URL)


async def get_or_create_user(telegram_id: int, username: str | None) -> User:
    """Get an existing user or create a new one with default settings."""
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if user is None:
            user = User(telegram_id=telegram_id, username=username)
            session.add(user)
            await session.flush()
            user.settings = UserSettings(user_id=user.id)
            await session.commit()
            logger.info("New user created: telegram_id=%s, username=%s", telegram_id, username)
        else:
            if user.username != username:
                user.username = username
                await session.commit()
        return user


async def get_user_settings(user_id: int) -> UserSettings:
    """Get user settings, creating defaults if missing."""
    async with async_session() as session:
        result = await session.execute(
            select(UserSettings).where(UserSettings.user_id == user_id)
        )
        settings = result.scalar_one_or_none()
        if settings is None:
            settings = UserSettings(user_id=user_id)
            session.add(settings)
            await session.commit()
        return settings


async def update_user_settings(user_id: int, **kwargs) -> None:
    """Update specific user setting fields."""
    async with async_session() as session:
        await session.execute(
            update(UserSettings).where(UserSettings.user_id == user_id).values(**kwargs)
        )
        await session.commit()


async def create_download(user_id: int, url: str, **kwargs) -> Download:
    """Create a new download record."""
    async with async_session() as session:
        dl = Download(user_id=user_id, url=url, **kwargs)
        session.add(dl)
        await session.commit()
        await session.refresh(dl)
        return dl


async def update_download(download_id: int, **kwargs) -> None:
    """Update a download record."""
    async with async_session() as session:
        await session.execute(
            update(Download).where(Download.id == download_id).values(**kwargs)
        )
        await session.commit()


async def get_user_downloads(user_id: int, limit: int = 20) -> list[Download]:
    """Get recent downloads for a user."""
    async with async_session() as session:
        result = await session.execute(
            select(Download)
            .where(Download.user_id == user_id)
            .order_by(Download.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


async def get_all_users_count() -> int:
    """Count all registered users."""
    from sqlalchemy import func
    async with async_session() as session:
        result = await session.execute(select(func.count(User.id)))
        return result.scalar_one()


async def get_today_downloads_stats() -> dict:
    """Get download statistics for today."""
    from sqlalchemy import func
    from datetime import datetime, timedelta
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    async with async_session() as session:
        # Total today
        total_result = await session.execute(
            select(func.count(Download.id)).where(Download.created_at >= today_start)
        )
        total = total_result.scalar_one()

        # By media type
        video_result = await session.execute(
            select(func.count(Download.id)).where(
                Download.created_at >= today_start,
                Download.media_type == "video",
            )
        )
        video = video_result.scalar_one()

        audio_result = await session.execute(
            select(func.count(Download.id)).where(
                Download.created_at >= today_start,
                Download.media_type == "audio",
            )
        )
        audio = audio_result.scalar_one()

        # Success/errors
        success_result = await session.execute(
            select(func.count(Download.id)).where(
                Download.created_at >= today_start,
                Download.status == "done",
            )
        )
        success = success_result.scalar_one()

        error_result = await session.execute(
            select(func.count(Download.id)).where(
                Download.created_at >= today_start,
                Download.status == "error",
            )
        )
        errors = error_result.scalar_one()

        return {
            "total": total,
            "video": video,
            "audio": audio,
            "success": success,
            "errors": errors,
        }
