"""
Media Downloader Bot — main entry point.

Starts the Telegram bot, initializes database, registers handlers,
and runs the cleanup background task.
"""
import asyncio
import logging
import os
import time
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command

from config import config
from database.database import init_db
from services.download_service import init_download_service
from bot.handlers import start, help, download, playlist, settings, admin

# === Logging setup ===
config.ensure_dirs()

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[
        logging.FileHandler(config.LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


async def cleanup_temp_files():
    """Background task: delete temp files older than 1 hour."""
    while True:
        await asyncio.sleep(300)  # Check every 5 minutes
        try:
            cutoff = time.time() - (config.TEMP_FILE_TTL_HOURS * 3600)
            removed = 0
            for f in config.TEMP_DIR.rglob("*"):
                if f.is_file():
                    try:
                        if f.stat().st_mtime < cutoff:
                            os.remove(str(f))
                            removed += 1
                    except SystemExit:
                        pass
                    except Exception:
                        pass
            if removed > 0:
                logger.info("Cleanup: removed %d temp files", removed)
        except Exception as e:
            logger.error("Cleanup error: %s", e)


async def main():
    """Main entry point."""
    if not config.BOT_TOKEN or config.BOT_TOKEN == "your_bot_token_here":
        logger.error("BOT_TOKEN not set! Create a .env file with your token from @BotFather.")
        logger.error("Example: cp .env.example .env && edit .env")
        return

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Create bot and dispatcher
    use_local = config.USE_LOCAL_BOT_API and config.API_ID and config.API_HASH
    if not config.USE_LOCAL_BOT_API:
        pass  # cloud Bot API (50 MB limit)
    elif not use_local:
        logger.warning(
            "USE_LOCAL_BOT_API=true but API_ID/API_HASH not set — "
            "falling back to cloud Bot API (50 MB limit). "
            "Get credentials at https://my.telegram.org and fill API_ID/API_HASH in .env, "
            "then start start_bot_api.sh before launching the bot."
        )

    if use_local:
        from aiogram.client.session.aiohttp import AiohttpSession
        session = AiohttpSession() if not config.PROXY_URL else AiohttpSession(proxy=config.PROXY_URL)
        bot = Bot(
            token=config.BOT_TOKEN,
            base_url=config.LOCAL_BOT_API_URL,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
            session=session,
        )
        logger.info("Using LOCAL Bot API server: %s (file limit %d MB)", config.LOCAL_BOT_API_URL, config.TELEGRAM_FILE_LIMIT_MB)
    elif config.PROXY_URL:
        from aiogram.client.session.aiohttp import AiohttpSession
        session = AiohttpSession(proxy=config.PROXY_URL)
        bot = Bot(
            token=config.BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
            session=session,
        )
        logger.info("Using cloud Bot API with proxy: %s (file limit 50 MB)", config.PROXY_URL)
    else:
        bot = Bot(
            token=config.BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
        logger.info("Using cloud Bot API (file limit 50 MB)")
    dp = Dispatcher()

    # Initialize download service
    init_download_service(bot)
    logger.info("Download service initialized")

    # Set bot commands
    from aiogram.types import BotCommand
    await bot.set_my_commands([
        BotCommand(command="start", description="Start the bot"),
        BotCommand(command="help", description="Show help"),
        BotCommand(command="settings", description="User settings"),
        BotCommand(command="cancel", description="Cancel current operation"),
        BotCommand(command="admin", description="Admin panel (admins only)"),
    ])

    # Register routers
    dp.include_router(start.router)
    dp.include_router(help.router)
    dp.include_router(settings.router)
    dp.include_router(download.router)
    dp.include_router(playlist.router)
    dp.include_router(admin.router)

    # Start cleanup task
    asyncio.create_task(cleanup_temp_files())

    # Delete webhook and start polling
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Bot started successfully!")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("Bot stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped by user")
