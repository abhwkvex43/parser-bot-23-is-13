"""
Telegram file sending service.
Handles sending files to users with size limit checks.
"""
import logging
from pathlib import Path

from aiogram import Bot
from aiogram.types import (
    FSInputFile,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.exceptions import TelegramBadRequest

from config import config
from services.conversion_service import get_file_size_mb

logger = logging.getLogger(__name__)


async def send_file(
    bot: Bot,
    chat_id: int,
    file_path: Path,
    caption: str = "",
    reply_markup: InlineKeyboardMarkup | None = None,
) -> bool:
    """Send a file to a Telegram user.

    Checks file size against Telegram limits before sending.
    Returns True if sent, False if file is too large.
    """
    if not file_path.exists():
        logger.error("File not found: %s", file_path)
        return False

    size_mb = get_file_size_mb(file_path)

    if size_mb > config.TELEGRAM_FILE_LIMIT_MB:
        logger.warning(
            "File too large for Telegram: %.1f MB (limit %d MB) — %s",
            size_mb,
            config.TELEGRAM_FILE_LIMIT_MB,
            file_path,
        )
        return False

    try:
        file = FSInputFile(str(file_path))
        await bot.send_document(
            chat_id=chat_id,
            document=file,
            caption=caption[:1024] if caption else None,
            reply_markup=reply_markup,
        )
        logger.info("File sent: %s (%.1f MB)", file_path.name, size_mb)
        return True
    except TelegramBadRequest as e:
        if "file is too big" in str(e).lower():
            logger.warning("Telegram rejected file (too big): %s", file_path)
            return False
        logger.error("Telegram API error: %s", e)
        raise
    except Exception as e:
        logger.error("Failed to send file: %s", e)
        raise


def format_result_caption(
    title: str,
    file_size_mb: float,
    quality: str,
    fmt: str,
    subtitle_info: str = "",
    media_type: str = "video",
) -> str:
    """Format the result message caption."""
    emoji = "\U0001F3AC" if media_type == "video" else "\U0001F3B5"
    quality_label = quality if media_type == "video" else f"{quality} kbps"

    lines = [
        f"\u2705 \u0413\u043e\u0442\u043e\u0432\u043e!",
        "",
        f"{emoji} {title}",
        f"\U0001F4E6 \u0420\u0430\u0437\u043c\u0435\u0440: {file_size_mb:.1f} MB",
    ]
    if media_type == "video":
        lines.append(f"\U0001F39F \u041a\u0430\u0447\u0435\u0441\u0442\u0432\u043e: {quality_label}")
    lines.append(f"\U0001F4C1 \u0424\u043e\u0440\u043c\u0430\u0442: {fmt.upper()}")
    if subtitle_info:
        lines.append(f"\U0001F4DD \u0421\u0443\u0431\u0442\u0438\u0442\u0440\u044b: {subtitle_info}")

    return "\n".join(lines)


def build_result_keyboard() -> InlineKeyboardMarkup:
    """Build the post-download result keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="\U0001F517 \u0421\u043a\u0430\u0447\u0430\u0442\u044c \u0435\u0449\u0435", callback_data="download_again"),
            InlineKeyboardButton(text="\U0001F4E5 \u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c \u0432 \u043e\u0447\u0435\u0440\u0435\u0434\u044c", callback_data="add_to_queue"),
        ],
        [
            InlineKeyboardButton(text="\U0001F4CB \u041c\u043e\u0438 \u0437\u0430\u0433\u0440\u0443\u0437\u043a\u0438", callback_data="my_downloads"),
        ],
    ])
