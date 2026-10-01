"""
Settings command handler.
"""
import logging

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from database import database as db
from utils.safe_edit import safe_edit
from bot.keyboards.main import back_to_main_kb

logger = logging.getLogger(__name__)

router = Router()


def _settings_text(settings) -> str:
    """Format settings display text."""
    sub_status = "\u0411\u0435\u0437 \u0441\u0443\u0431\u0442\u0438\u0442\u0440\u043e\u0432"
    if settings.subtitle_enabled:
        lang_names = {"ru": "\u0420\u0443\u0441\u0441\u043a\u0438\u0439", "en": "English", "de": "Deutsch", "it": "Italiano"}
        sub_status = lang_names.get(settings.subtitle_language, settings.subtitle_language)

    _mt = "\u0412\u0438\u0434\u0435\u043e" if settings.media_type == "video" else "\u0410\u0443\u0434\u0438\u043e"
    return (
        "\u2699\ufe0f <b>\u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438</b>\n\n"
        f"\U0001F3AC <b>\u0422\u0438\u043f \u043f\u043e \u0443\u043c\u043e\u043b\u0447\u0430\u043d\u0438\u044e:</b>\n"
        f"{_mt}\n\n"
        f"\U0001F4F1 <b>\u041a\u0430\u0447\u0435\u0441\u0442\u0432\u043e \u0432\u0438\u0434\u0435\u043e:</b>\n"
        f"{settings.video_quality}\n\n"
        f"\U0001F4C1 <b>\u0424\u043e\u0440\u043c\u0430\u0442 \u0432\u0438\u0434\u0435\u043e:</b>\n"
        f"{settings.video_format.upper()}\n\n"
        f"\U0001F3B5 <b>\u0424\u043e\u0440\u043c\u0430\u0442 \u0430\u0443\u0434\u0438\u043e:</b>\n"
        f"{settings.audio_format.upper()}\n\n"
        f"\U0001F3A7 <b>\u041a\u0430\u0447\u0435\u0441\u0442\u0432\u043e \u0430\u0443\u0434\u0438\u043e:</b>\n"
        f"{settings.audio_quality} kbps\n\n"
        f"\U0001F4DD <b>\u0421\u0443\u0431\u0442\u0438\u0442\u0440\u044b:</b>\n"
        f"{sub_status}\n\n"
        "<i>\u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438 \u0441\u043e\u0445\u0440\u0430\u043d\u044f\u044e\u0442\u0441\u044f \u043c\u0435\u0436\u0434\u0443 \u0437\u0430\u043f\u0440\u043e\u0441\u0430\u043c\u0438.</i>"
    )


def _settings_kb(settings) -> "InlineKeyboardMarkup":
    """Build settings editing keyboard."""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    _mt = "\u0412\u0438\u0434\u0435\u043e" if settings.media_type == "video" else "\u0410\u0443\u0434\u0438\u043e"
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"\U0001F3AC \u0422\u0438\u043f: {_mt}",
                callback_data="set_media_type",
            )
        ],
        [
            InlineKeyboardButton(text=f"\U0001F4F1 \u041a\u0430\u0447\u0435\u0441\u0442\u0432\u043e: {settings.video_quality}", callback_data="set_video_quality"),
            InlineKeyboardButton(text=f"\U0001F4C1 \u0424\u043e\u0440\u043c\u0430\u0442: {settings.video_format.upper()}", callback_data="set_video_format"),
        ],
        [
            InlineKeyboardButton(text=f"\U0001F3A7 \u0410\u0443\u0434\u0438\u043e: {settings.audio_quality} kbps", callback_data="set_audio_quality"),
            InlineKeyboardButton(text=f"\U0001F3B5 \u0424\u043e\u0440\u043c\u0430\u0442: {settings.audio_format.upper()}", callback_data="set_audio_format"),
        ],
        [
            InlineKeyboardButton(text="\U0001F4DD \u0421\u0443\u0431\u0442\u0438\u0442\u0440\u044b", callback_data="set_subtitles"),
        ],
        [
            InlineKeyboardButton(text="\u2b05\ufe0f \u041d\u0430\u0437\u0430\u0434 \u0432 \u043c\u0435\u043d\u044e", callback_data="main_menu"),
        ],
    ])


@router.message(Command("settings"))
async def cmd_settings(message: Message):
    """Show user settings via /settings command."""
    user = await db.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
    )
    settings = await db.get_user_settings(user.id)
    await message.answer(_settings_text(settings), reply_markup=_settings_kb(settings))


@router.callback_query(F.data == "settings")
async def cb_settings(callback: CallbackQuery):
    """Show user settings via inline button."""
    user = await db.get_or_create_user(callback.from_user.id, callback.from_user.username)
    settings = await db.get_user_settings(user.id)
    await safe_edit(callback.message,_settings_text(settings), reply_markup=_settings_kb(settings))
    await callback.answer()


@router.callback_query(F.data == "set_media_type")
async def set_media_type(callback: CallbackQuery):
    """Toggle media type."""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    user = await db.get_or_create_user(callback.from_user.id, callback.from_user.username)
    settings = await db.get_user_settings(user.id)
    new_type = "audio" if settings.media_type == "video" else "video"
    await db.update_user_settings(user.id, media_type=new_type)

    settings.media_type = new_type
    await safe_edit(callback.message,_settings_text(settings), reply_markup=_settings_kb(settings))
    await callback.answer()


@router.callback_query(F.data == "set_video_quality")
async def set_video_quality(callback: CallbackQuery):
    """Cycle video quality."""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    user = await db.get_or_create_user(callback.from_user.id, callback.from_user.username)
    settings = await db.get_user_settings(user.id)
    qualities = ["360p", "480p", "720p", "1080p", "best"]
    current_idx = qualities.index(settings.video_quality) if settings.video_quality in qualities else 2
    new_quality = qualities[(current_idx + 1) % len(qualities)]
    await db.update_user_settings(user.id, video_quality=new_quality)

    settings.video_quality = new_quality
    await safe_edit(callback.message,_settings_text(settings), reply_markup=_settings_kb(settings))
    await callback.answer()


@router.callback_query(F.data == "set_video_format")
async def set_video_format(callback: CallbackQuery):
    """Cycle video format."""
    user = await db.get_or_create_user(callback.from_user.id, callback.from_user.username)
    settings = await db.get_user_settings(user.id)
    formats = ["mp4", "mkv", "webm"]
    current_idx = formats.index(settings.video_format) if settings.video_format in formats else 0
    new_format = formats[(current_idx + 1) % len(formats)]
    await db.update_user_settings(user.id, video_format=new_format)

    settings.video_format = new_format
    await safe_edit(callback.message,_settings_text(settings), reply_markup=_settings_kb(settings))
    await callback.answer()


@router.callback_query(F.data == "set_audio_quality")
async def set_audio_quality(callback: CallbackQuery):
    """Cycle audio quality."""
    user = await db.get_or_create_user(callback.from_user.id, callback.from_user.username)
    settings = await db.get_user_settings(user.id)
    qualities = ["128", "192", "256", "320", "best"]
    current_idx = qualities.index(settings.audio_quality) if settings.audio_quality in qualities else 3
    new_quality = qualities[(current_idx + 1) % len(qualities)]
    await db.update_user_settings(user.id, audio_quality=new_quality)

    settings.audio_quality = new_quality
    await safe_edit(callback.message,_settings_text(settings), reply_markup=_settings_kb(settings))
    await callback.answer()


@router.callback_query(F.data == "set_audio_format")
async def set_audio_format(callback: CallbackQuery):
    """Cycle audio format."""
    user = await db.get_or_create_user(callback.from_user.id, callback.from_user.username)
    settings = await db.get_user_settings(user.id)
    formats = ["mp3", "m4a", "opus", "wav", "flac"]
    current_idx = formats.index(settings.audio_format) if settings.audio_format in formats else 0
    new_format = formats[(current_idx + 1) % len(formats)]
    await db.update_user_settings(user.id, audio_format=new_format)

    settings.audio_format = new_format
    await safe_edit(callback.message,_settings_text(settings), reply_markup=_settings_kb(settings))
    await callback.answer()


@router.callback_query(F.data == "set_subtitles")
async def set_subtitles(callback: CallbackQuery):
    """Toggle subtitles and cycle language."""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    user = await db.get_or_create_user(callback.from_user.id, callback.from_user.username)
    settings = await db.get_user_settings(user.id)

    if not settings.subtitle_enabled:
        await db.update_user_settings(user.id, subtitle_enabled=True, subtitle_language="ru")
    else:
        langs = ["ru", "en", "de", "it", "fr", "es"]
        current_idx = langs.index(settings.subtitle_language) if settings.subtitle_language in langs else 0
        next_idx = current_idx + 1
        if next_idx >= len(langs):
            await db.update_user_settings(user.id, subtitle_enabled=False)
        else:
            await db.update_user_settings(user.id, subtitle_language=langs[next_idx])

    settings = await db.get_user_settings(user.id)
    await safe_edit(callback.message,_settings_text(settings), reply_markup=_settings_kb(settings))
    await callback.answer()
