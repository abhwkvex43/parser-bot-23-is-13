"""
Download handler — main download flow:
URL -> analyze -> select type -> select quality -> select format -> subtitles -> download -> send.
"""
import logging
import os

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from config import config
from database import database as db
from downloader import video as video_module
from downloader import subtitles as subtitle_module
from utils.validators import is_valid_url, detect_url_type
from utils.progress import format_duration, DownloadProgress
from utils.safe_edit import safe_edit
from bot.states.download_states import DownloadStates
from bot.keyboards.main import media_type_kb, cancel_kb, back_to_main_kb
from bot.keyboards.quality import (
    video_quality_kb, audio_quality_kb, subtitle_lang_kb,
)
from bot.keyboards.formats import (
    video_format_kb, audio_format_kb, subtitle_format_kb, subtitle_mode_kb,
)

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data == "download")
async def cb_download(callback: CallbackQuery, state: FSMContext):
    """Start download flow — ask for URL."""
    await state.set_state(DownloadStates.waiting_for_url)
    await safe_edit(callback.message,
        "\U0001F4E5 <b>\u0417\u0430\u0433\u0440\u0443\u0437\u043a\u0430 \u043c\u0435\u0434\u0438\u0430</b>\n\n"
        "\u041e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 \u0441\u0441\u044b\u043b\u043a\u0443 \u043d\u0430 \u0432\u0438\u0434\u0435\u043e \u0438\u043b\u0438 \u0430\u0443\u0434\u0438\u043e.\n"
        "\u041d\u0430\u043f\u0440\u0438\u043c\u0435\u0440:\n"
        "<code>https://www.youtube.com/watch?v=...</code>",
        reply_markup=cancel_kb(),
    )
    await callback.answer()


@router.message(DownloadStates.waiting_for_url)
async def process_url(message: Message, state: FSMContext):
    """Receive URL and start analysis."""
    url = message.text.strip() if message.text else ""

    if not is_valid_url(url):
        await message.answer(
            "\u274c \u0421\u0441\u044b\u043b\u043a\u0430 \u043d\u0435 \u0440\u0430\u0441\u043f\u043e\u0437\u043d\u0430\u043d\u0430.\n"
            "\u041f\u0440\u043e\u0432\u0435\u0440\u044c\u0442\u0435 URL \u0438 \u043f\u043e\u043f\u0440\u043e\u0431\u0443\u0439\u0442\u0435 \u0435\u0449\u0435 \u0440\u0430\u0437.",
            reply_markup=cancel_kb(),
        )
        return

    url_type = detect_url_type(url)

    if url_type == "playlist":
        # Redirect to playlist flow
        await state.clear()
        from bot.handlers.playlist import handle_playlist_url
        await handle_playlist_url(message, state, url)
        return

    await state.set_state(DownloadStates.analyzing)
    status_msg = await message.answer("\U0001F50D \u0410\u043d\u0430\u043b\u0438\u0437 \u043c\u0435\u0434\u0438\u0430...")

    try:
        info = await video_module.get_video_info(url)

        if not info or not info.get("title"):
            await safe_edit(status_msg,
                "\u274c \u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c \u043f\u043e\u043b\u0443\u0447\u0438\u0442\u044c \u0432\u0438\u0434\u0435\u043e.\n"
                "\u0412\u043e\u0437\u043c\u043e\u0436\u043d\u043e, \u043e\u043d\u043e \u0443\u0434\u0430\u043b\u0435\u043d\u043e, \u0437\u0430\u043a\u0440\u044b\u0442\u043e "
                "\u0438\u043b\u0438 \u043d\u0435\u0434\u043e\u0441\u0442\u0443\u043f\u043d\u043e \u0434\u043b\u044f \u0437\u0430\u0433\u0440\u0443\u0437\u043a\u0438.",
                reply_markup=cancel_kb(),
            )
            await state.clear()
            return

        # Store info in state
        await state.update_data(
            url=url,
            title=info.get("title", "Unknown"),
            uploader=info.get("uploader"),
            duration=info.get("duration", 0),
            available_qualities=info.get("available_qualities", []),
            subtitle_languages=info.get("subtitle_languages", []),
        )

        # Format info message
        duration_str = format_duration(info.get("duration", 0))
        size_str = DownloadProgress.format_size(info.get("filesize_approx", 0)) if info.get("filesize_approx") else "~"
        max_quality = info.get("available_qualities", [])
        max_quality_str = max_quality[-1] if max_quality else "\u043d\u0435\u0438\u0437\u0432\u0435\u0441\u0442\u043d\u043e"

        info_text = (
            f"\U0001F3AC <b>{info.get('title', 'Unknown')}</b>\n\n"
            f"\U0001F464 <b>\u0410\u0432\u0442\u043e\u0440:</b>\n{info.get('uploader', 'Unknown')}\n\n"
            f"\u23f1 <b>\u0414\u043b\u0438\u0442\u0435\u043b\u044c\u043d\u043e\u0441\u0442\u044c:</b>\n{duration_str}\n\n"
            f"\U0001F441 <b>\u0420\u0430\u0437\u0440\u0435\u0448\u0435\u043d\u0438\u0435:</b>\n\u0434\u043e {max_quality_str}\n\n"
            f"\U0001F4be <b>\u041f\u0440\u0438\u043c\u0435\u0440\u043d\u044b\u0439 \u0440\u0430\u0437\u043c\u0435\u0440:</b>\n{size_str}\n\n"
            "\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0442\u0438\u043f \u0437\u0430\u0433\u0440\u0443\u0437\u043a\u0438:"
        )

        await safe_edit(status_msg,info_text, reply_markup=media_type_kb())
        await state.set_state(DownloadStates.selecting_type)

    except Exception as e:
        logger.error("Analysis failed: %s", e)
        error_msg = str(e)
        if "private" in error_msg.lower() or "unavailable" in error_msg.lower():
            user_msg = "\u274c \u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c \u043f\u043e\u043b\u0443\u0447\u0438\u0442\u044c \u0432\u0438\u0434\u0435\u043e. \u0412\u043e\u0437\u043c\u043e\u0436\u043d\u043e, \u043e\u043d\u043e \u0443\u0434\u0430\u043b\u0435\u043d\u043e \u0438\u043b\u0438 \u0437\u0430\u043a\u0440\u044b\u0442\u043e."
        elif "429" in error_msg or "rate" in error_msg.lower():
            user_msg = "\u26a0\ufe0f \u0418\u0441\u0442\u043e\u0447\u043d\u0438\u043a \u0432\u0440\u0435\u043c\u0435\u043d\u043d\u043e \u043e\u0433\u0440\u0430\u043d\u0438\u0447\u0438\u043b \u0437\u0430\u043f\u0440\u043e\u0441\u044b. \u041f\u043e\u043f\u0440\u043e\u0431\u0443\u0439\u0442\u0435 \u043f\u043e\u0437\u0436\u0435."
        else:
            user_msg = f"\u274c \u041e\u0448\u0438\u0431\u043a\u0430 \u0430\u043d\u0430\u043b\u0438\u0437\u0430: {error_msg[:200]}"
        await safe_edit(status_msg,user_msg, reply_markup=cancel_kb())
        await state.clear()


# === Type selection ===

@router.callback_query(F.data == "type_video", DownloadStates.selecting_type)
async def select_video(callback: CallbackQuery, state: FSMContext):
    """User selected video — show quality options."""
    data = await state.get_data()
    available = data.get("available_qualities", [])

    await safe_edit(callback.message,
        "\U0001F3AC \u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u043a\u0430\u0447\u0435\u0441\u0442\u0432\u043e:",
        reply_markup=video_quality_kb(available),
    )
    await state.set_state(DownloadStates.selecting_video_quality)
    await callback.answer()


@router.callback_query(F.data == "type_audio", DownloadStates.selecting_type)
async def select_audio(callback: CallbackQuery, state: FSMContext):
    """User selected audio — show quality options."""
    await safe_edit(callback.message,
        "\U0001F3B5 \u041a\u0430\u0447\u0435\u0441\u0442\u0432\u043e:",
        reply_markup=audio_quality_kb(),
    )
    await state.set_state(DownloadStates.selecting_audio_quality)
    await callback.answer()


@router.callback_query(F.data == "type_subtitles", DownloadStates.selecting_type)
async def select_subtitles(callback: CallbackQuery, state: FSMContext):
    """User selected subtitles — show language options."""
    data = await state.get_data()
    available_langs = data.get("subtitle_languages", [])

    await safe_edit(callback.message,
        "\U0001F4DD \u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u044f\u0437\u044b\u043a \u0441\u0443\u0431\u0442\u0438\u0442\u0440\u043e\u0432:",
        reply_markup=subtitle_lang_kb(available_langs),
    )
    await state.set_state(DownloadStates.selecting_subtitle_lang)
    await callback.answer()


# === Video quality ===

@router.callback_query(F.data.startswith("vq_"), DownloadStates.selecting_video_quality)
async def select_video_quality(callback: CallbackQuery, state: FSMContext):
    """Video quality selected — show format options."""
    quality = callback.data.split("_", 1)[1]

    await state.update_data(quality=quality)
    await safe_edit(callback.message,
        f"\U0001F3AC \u0412\u044b\u0431\u0440\u0430\u043d\u043e \u043a\u0430\u0447\u0435\u0441\u0442\u0432\u043e: {quality}\n\n"
        "\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0444\u043e\u0440\u043c\u0430\u0442:",
        reply_markup=video_format_kb(quality),
    )
    await state.set_state(DownloadStates.selecting_video_format)
    await callback.answer()


# === Video format ===

@router.callback_query(F.data.startswith("vfmt_"), DownloadStates.selecting_video_format)
async def select_video_format(callback: CallbackQuery, state: FSMContext):
    """Video format selected — ask about subtitles."""
    parts = callback.data.split("_")
    fmt = parts[1]
    quality = parts[2] if len(parts) > 2 else "best"

    await state.update_data(format=fmt, quality=quality, media_type="video")

    # Ask about subtitles
    data = await state.get_data()
    available_langs = data.get("subtitle_languages", [])

    if available_langs:
        await safe_edit(callback.message,
            "\U0001F4DD \u0421\u0443\u0431\u0442\u0438\u0442\u0440\u044b\n\n"
            "\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u044f\u0437\u044b\u043a \u0441\u0443\u0431\u0442\u0438\u0442\u0440\u043e\u0432:",
            reply_markup=subtitle_lang_kb(available_langs),
        )
        await state.set_state(DownloadStates.selecting_subtitle_lang)
    else:
        # No subtitles available — proceed to download
        await _start_video_download(callback, state, subtitle_lang=None, embed_subs=False)

    await callback.answer()


# === Audio quality ===

@router.callback_query(F.data.startswith("aq_"), DownloadStates.selecting_audio_quality)
async def select_audio_quality(callback: CallbackQuery, state: FSMContext):
    """Audio quality selected — show format options."""
    quality = callback.data.split("_", 1)[1]

    await state.update_data(quality=quality)
    await safe_edit(callback.message,
        f"\U0001F3A7 \u0412\u044b\u0431\u0440\u0430\u043d\u043e \u043a\u0430\u0447\u0435\u0441\u0442\u0432\u043e: {quality} kbps\n\n"
        "\U0001F3B5 \u0424\u043e\u0440\u043c\u0430\u0442:",
        reply_markup=audio_format_kb(quality),
    )
    await state.set_state(DownloadStates.selecting_audio_format)
    await callback.answer()


# === Audio format ===

@router.callback_query(F.data.startswith("afmt_"), DownloadStates.selecting_audio_format)
async def select_audio_format(callback: CallbackQuery, state: FSMContext):
    """Audio format selected — start download."""
    parts = callback.data.split("_")
    fmt = parts[1]
    quality = parts[2] if len(parts) > 2 else "320"

    await state.update_data(format=fmt, quality=quality, media_type="audio")

    await _start_audio_download(callback, state)


# === Subtitle language ===

@router.callback_query(F.data.startswith("slang_"), DownloadStates.selecting_subtitle_lang)
async def select_subtitle_lang(callback: CallbackQuery, state: FSMContext):
    """Subtitle language selected."""
    lang = callback.data.split("_", 1)[1]

    if lang == "none":
        await state.update_data(subtitle_lang=None, embed_subs=False)
        # Proceed to download
        data = await state.get_data()
        if data.get("media_type") == "video":
            await _start_video_download(callback, state, subtitle_lang=None, embed_subs=False)
        else:
            await _start_audio_download(callback, state)
        return

    await state.update_data(subtitle_lang=lang)

    data = await state.get_data()
    if data.get("media_type") == "video":
        # Ask subtitle mode
        await safe_edit(callback.message,
            f"\U0001F4DD \u042f\u0437\u044b\u043a: {lang}\n\n"
            "\u041a\u0430\u043a \u043f\u0440\u0438\u043c\u0435\u043d\u0438\u0442\u044c \u0441\u0443\u0431\u0442\u0438\u0442\u0440\u044b?",
            reply_markup=subtitle_mode_kb(),
        )
        await state.set_state(DownloadStates.selecting_subtitle_mode)
    elif data.get("media_type") == "subtitles":
        # Subtitle format
        await safe_edit(callback.message,
            "\U0001F4DD \u0424\u043e\u0440\u043c\u0430\u0442 \u0441\u0443\u0431\u0442\u0438\u0442\u0440\u043e\u0432:",
            reply_markup=subtitle_format_kb(),
        )
        await state.set_state(DownloadStates.selecting_subtitle_format)
    else:
        # Audio with no subtitle context — proceed
        await _start_audio_download(callback, state)

    await callback.answer()


# === Subtitle mode (for video) ===

@router.callback_query(F.data.startswith("smode_"), DownloadStates.selecting_subtitle_mode)
async def select_subtitle_mode(callback: CallbackQuery, state: FSMContext):
    """Subtitle mode selected — start video download."""
    mode = callback.data.split("_", 1)[1]
    data = await state.get_data()
    lang = data.get("subtitle_lang")

    embed = mode == "embed"
    await _start_video_download(callback, state, subtitle_lang=lang, embed_subs=embed)


# === Subtitle format (for subtitles-only download) ===

@router.callback_query(F.data.startswith("sfmt_"), DownloadStates.selecting_subtitle_format)
async def select_subtitle_format(callback: CallbackQuery, state: FSMContext):
    """Subtitle format selected — download subtitles only."""
    fmt = callback.data.split("_", 1)[1]
    data = await state.get_data()

    await state.set_state(DownloadStates.downloading)
    await safe_edit(callback.message,
        "\U0001F4DD \u0417\u0430\u0433\u0440\u0443\u0437\u043a\u0430 \u0441\u0443\u0431\u0442\u0438\u0442\u0440\u043e\u0432...",
    )
    await callback.answer()

    url = data.get("url", "")
    title = data.get("title", "subtitles")
    lang = data.get("subtitle_lang", "ru")

    try:
        file_path = await subtitle_module.download(
            url=url,
            title=title,
            lang=lang,
            fmt=fmt,
            user_id=callback.from_user.id,
        )

        if file_path and file_path.exists():
            from aiogram.types import FSInputFile
            file = FSInputFile(str(file_path))
            await callback.message.answer_document(
                document=file,
                caption=f"\u2705 \u0421\u0443\u0431\u0442\u0438\u0442\u0440\u044b \u0433\u043e\u0442\u043e\u0432\u044b!\n\n"
                        f"\U0001F3AC {title}\n"
                        f"\U0001F310 \u042f\u0437\u044b\u043a: {lang}\n"
                        f"\U0001F4C1 \u0424\u043e\u0440\u043c\u0430\u0442: {fmt.upper()}",
            )
            # Clean up
            try:
                os.remove(str(file_path))
            except SystemExit:
                pass
            except Exception:
                pass
        else:
            await callback.message.answer(
                "\u274c \u0421\u0443\u0431\u0442\u0438\u0442\u0440\u044b \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u044b \u0434\u043b\u044f "
                f"\u044f\u0437\u044b\u043a\u0430 {lang}.",
            )

    except Exception as e:
        logger.error("Subtitle download failed: %s", e)
        await callback.message.answer(f"\u274c \u041e\u0448\u0438\u0431\u043a\u0430: {e}")

    await state.clear()


# === Back navigation ===

@router.callback_query(F.data == "back_to_quality", DownloadStates.selecting_video_format)
async def back_to_quality(callback: CallbackQuery, state: FSMContext):
    """Go back to quality selection."""
    data = await state.get_data()
    available = data.get("available_qualities", [])
    await safe_edit(callback.message,
        "\U0001F3AC \u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u043a\u0430\u0447\u0435\u0441\u0442\u0432\u043e:",
        reply_markup=video_quality_kb(available),
    )
    await state.set_state(DownloadStates.selecting_video_quality)
    await callback.answer()


@router.callback_query(F.data == "back_to_audio_quality", DownloadStates.selecting_audio_format)
async def back_to_audio_quality(callback: CallbackQuery, state: FSMContext):
    """Go back to audio quality selection."""
    await safe_edit(callback.message,
        "\U0001F3B5 \u041a\u0430\u0447\u0435\u0441\u0442\u0432\u043e:",
        reply_markup=audio_quality_kb(),
    )
    await state.set_state(DownloadStates.selecting_audio_quality)
    await callback.answer()


# === Cancel ===

@router.callback_query(F.data == "cancel_action")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    """Cancel current operation."""
    await state.clear()
    await safe_edit(callback.message,
        "\u274c \u041e\u043f\u0435\u0440\u0430\u0446\u0438\u044f \u043e\u0442\u043c\u0435\u043d\u0435\u043d\u0430.",
        reply_markup=back_to_main_kb(),
    )
    await callback.answer()


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """Cancel command."""
    await state.clear()
    from bot.keyboards.main import main_menu_kb
    await message.answer(
        "\u274c \u041e\u043f\u0435\u0440\u0430\u0446\u0438\u044f \u043e\u0442\u043c\u0435\u043d\u0435\u043d\u0430.",
        reply_markup=main_menu_kb(),
    )


# === Cancel download task ===

@router.callback_query(F.data.startswith("cancel_"))
async def cancel_download_task(callback: CallbackQuery):
    """Cancel a running download task."""
    task_id = callback.data.split("_", 1)[1]

    from services.queue_service import download_queue
    success = await download_queue.cancel_task(task_id)

    if success:
        await callback.answer("\u274c \u0417\u0430\u0433\u0440\u0443\u0437\u043a\u0430 \u043e\u0442\u043c\u0435\u043d\u0435\u043d\u0430", show_alert=True)
    else:
        await callback.answer("\u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c \u043e\u0442\u043c\u0435\u043d\u0438\u0442\u044c", show_alert=True)


# === Download again ===

@router.callback_query(F.data == "download_again")
async def download_again(callback: CallbackQuery, state: FSMContext):
    """Start a new download."""
    await state.set_state(DownloadStates.waiting_for_url)
    await safe_edit(callback.message,
        "\U0001F4E5 \u041e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 \u043d\u043e\u0432\u0443\u044e \u0441\u0441\u044b\u043b\u043a\u0443 \u0434\u043b\u044f \u0437\u0430\u0433\u0440\u0443\u0437\u043a\u0438.",
        reply_markup=cancel_kb(),
    )
    await callback.answer()


# === My downloads ===

@router.callback_query(F.data == "my_downloads")
async def show_my_downloads(callback: CallbackQuery):
    """Show user's download history."""
    user = await db.get_or_create_user(callback.from_user.id, callback.from_user.username)
    downloads = await db.get_user_downloads(user.id, limit=10)

    if not downloads:
        await safe_edit(callback.message,
            "\U0001F4CA <b>\u041c\u043e\u0438 \u0437\u0430\u0433\u0440\u0443\u0437\u043a\u0438</b>\n\n"
            "\u0418\u0441\u0442\u043e\u0440\u0438\u044f \u043f\u0443\u0441\u0442\u0430.",
            reply_markup=back_to_main_kb(),
        )
        await callback.answer()
        return

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    lines = ["\U0001F4CA <b>\u041c\u043e\u0438 \u0437\u0430\u0433\u0440\u0443\u0437\u043a\u0438</b>\n"]
    for dl in downloads[:10]:
        status_emoji = {
            "done": "\u2705", "error": "\u274c", "cancelled": "\U0001F6AB",
            "downloading": "\U0001F504", "pending": "\u23f3", "processing": "\u2699\ufe0f",
        }.get(dl.status, "\u2753")
        title = (dl.title or "Unknown")[:40]
        lines.append(f"{status_emoji} {title}")

    lines.append("")
    await safe_edit(callback.message,"\n".join(lines), reply_markup=back_to_main_kb())
    await callback.answer()


# === Add to queue ===

@router.callback_query(F.data == "add_to_queue")
async def add_to_queue(callback: CallbackQuery, state: FSMContext):
    """Add another URL to queue."""
    await state.set_state(DownloadStates.waiting_for_url)
    await safe_edit(callback.message,
        "\U0001F4E5 \u041e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 \u0441\u0441\u044b\u043b\u043a\u0443 \u0434\u043b\u044f \u0434\u043e\u0431\u0430\u0432\u043b\u0435\u043d\u0438\u044f \u0432 \u043e\u0447\u0435\u0440\u0435\u0434\u044c.",
        reply_markup=cancel_kb(),
    )
    await callback.answer()


# === Helper functions ===

async def _start_video_download(callback: CallbackQuery, state: FSMContext, subtitle_lang: str | None, embed_subs: bool):
    """Start video download with selected parameters."""
    from services.download_service import download_service

    data = await state.get_data()

    await state.set_state(DownloadStates.downloading)
    await safe_edit(callback.message,
        "\u2b07\ufe0f \u041d\u0430\u0447\u0438\u043d\u0430\u044e \u0437\u0430\u0433\u0440\u0443\u0437\u043a\u0443...",
    )
    await callback.answer()

    task_id = await download_service.start_download(
        user_id=callback.from_user.id,
        chat_id=callback.message.chat.id,
        url=data["url"],
        media_type="video",
        quality=data.get("quality", "best"),
        fmt=data.get("format", "mp4"),
        title=data.get("title", ""),
        uploader=data.get("uploader"),
        subtitle_lang=subtitle_lang,
        embed_subs=embed_subs,
    )

    if not task_id:
        await callback.message.answer("\u26a0\ufe0f \u041e\u0447\u0435\u0440\u0435\u0434\u044c \u0437\u0430\u0433\u0440\u0443\u0437\u043e\u043a \u0437\u0430\u043f\u043e\u043b\u043d\u0435\u043d\u0430.")

    await state.clear()


async def _start_audio_download(callback: CallbackQuery, state: FSMContext):
    """Start audio download with selected parameters."""
    from services.download_service import download_service

    data = await state.get_data()

    await state.set_state(DownloadStates.downloading)
    await safe_edit(callback.message,
        "\u2b07\ufe0f \u041d\u0430\u0447\u0438\u043d\u0430\u044e \u0437\u0430\u0433\u0440\u0443\u0437\u043a\u0443 \u0430\u0443\u0434\u0438\u043e...",
    )
    await callback.answer()

    task_id = await download_service.start_download(
        user_id=callback.from_user.id,
        chat_id=callback.message.chat.id,
        url=data["url"],
        media_type="audio",
        quality=data.get("quality", "320"),
        fmt=data.get("format", "mp3"),
        title=data.get("title", ""),
        uploader=data.get("uploader"),
    )

    if not task_id:
        await callback.message.answer("\u26a0\ufe0f \u041e\u0447\u0435\u0440\u0435\u0434\u044c \u0437\u0430\u0433\u0440\u0443\u0437\u043e\u043a \u0437\u0430\u043f\u043e\u043b\u043d\u0435\u043d\u0430.")

    await state.clear()
