"""
Playlist handler — playlist download flow:
URL -> analyze -> select all or range -> select type -> quality -> format -> subtitles -> download.
"""
import logging
import asyncio

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database import database as db
from downloader import playlist as playlist_module
from utils.validators import is_valid_url, detect_url_type, parse_playlist_range
from utils.progress import format_duration, format_total_duration
from utils.safe_edit import safe_edit
from bot.states.download_states import PlaylistStates
from bot.keyboards.main import cancel_kb, back_to_main_kb
from bot.keyboards.playlist import (
    playlist_action_kb, playlist_type_kb, playlist_quality_kb,
    playlist_audio_quality_kb, playlist_format_kb, playlist_audio_format_kb,
)

logger = logging.getLogger(__name__)

router = Router()


async def handle_playlist_url(message: Message, state: FSMContext, url: str):
    """Handle a playlist URL — analyze and show info."""
    await state.set_state(PlaylistStates.analyzing)
    status_msg = await message.answer("\U0001F50D \u0410\u043d\u0430\u043b\u0438\u0437 \u043f\u043b\u0435\u0439\u043b\u0438\u0441\u0442\u0430...")

    try:
        info = await playlist_module.get_playlist_info(url)

        if not info or not info.get("entries"):
            await safe_edit(status_msg,
                "\u274c \u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c \u043f\u043e\u043b\u0443\u0447\u0438\u0442\u044c \u043f\u043b\u0435\u0439\u043b\u0438\u0441\u0442.\n"
                "\u041f\u0440\u043e\u0432\u0435\u0440\u044c\u0442\u0435 \u0441\u0441\u044b\u043b\u043a\u0443.",
                reply_markup=cancel_kb(),
            )
            await state.clear()
            return

        await state.update_data(
            playlist_url=url,
            playlist_title=info.get("title", "Unknown"),
            playlist_entries=info.get("entries", []),
            playlist_count=info.get("total_count", 0),
            playlist_duration=info.get("total_duration", 0),
        )

        total_dur = format_total_duration(info.get("total_duration", 0))

        text = (
            f"\U0001F4CB <b>\u041f\u043b\u0435\u0439\u043b\u0438\u0441\u0442</b>\n\n"
            f"\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435:\n{info.get('title', 'Unknown')}\n\n"
            f"\u041a\u043e\u043b\u0438\u0447\u0435\u0441\u0442\u0432\u043e \u0432\u0438\u0434\u0435\u043e:\n{info.get('total_count', 0)}\n\n"
            f"\u041e\u0431\u0449\u0430\u044f \u0434\u043b\u0438\u0442\u0435\u043b\u044c\u043d\u043e\u0441\u0442\u044c:\n{total_dur}"
        )

        await safe_edit(status_msg,text, reply_markup=playlist_action_kb())
        await state.set_state(PlaylistStates.selecting_action)

    except Exception as e:
        logger.error("Playlist analysis failed: %s", e)
        await safe_edit(status_msg,
            f"\u274c \u041e\u0448\u0438\u0431\u043a\u0430 \u0430\u043d\u0430\u043b\u0438\u0437\u0430: {str(e)[:200]}",
            reply_markup=cancel_kb(),
        )
        await state.clear()


@router.callback_query(F.data == "playlist")
async def cb_playlist(callback: CallbackQuery, state: FSMContext):
    """Start playlist flow."""
    await state.set_state(PlaylistStates.waiting_for_url)
    await safe_edit(callback.message,
        "\U0001F4CB <b>\u0417\u0430\u0433\u0440\u0443\u0437\u043a\u0430 \u043f\u043b\u0435\u0439\u043b\u0438\u0441\u0442\u0430</b>\n\n"
        "\u041e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 \u0441\u0441\u044b\u043b\u043a\u0443 \u043d\u0430 \u043f\u043b\u0435\u0439\u043b\u0438\u0441\u0442.\n"
        "\u041d\u0430\u043f\u0440\u0438\u043c\u0435\u0440:\n"
        "<code>https://www.youtube.com/playlist?list=...</code>",
        reply_markup=cancel_kb(),
    )
    await callback.answer()


@router.message(PlaylistStates.waiting_for_url)
async def process_playlist_url(message: Message, state: FSMContext):
    """Receive playlist URL."""
    url = message.text.strip() if message.text else ""

    if not is_valid_url(url):
        await message.answer(
            "\u274c \u0421\u0441\u044b\u043b\u043a\u0430 \u043d\u0435 \u0440\u0430\u0441\u043f\u043e\u0437\u043d\u0430\u043d\u0430.",
            reply_markup=cancel_kb(),
        )
        return

    await handle_playlist_url(message, state, url)


# === Action selection ===

@router.callback_query(F.data == "pl_all", PlaylistStates.selecting_action)
async def playlist_all(callback: CallbackQuery, state: FSMContext):
    """Download entire playlist."""
    data = await state.get_data()
    entries = data.get("playlist_entries", [])

    # Select all indices
    await state.update_data(selected_indices=list(range(1, len(entries) + 1)))
    await _show_type_selection(callback, state)


@router.callback_query(F.data == "pl_select", PlaylistStates.selecting_action)
async def playlist_select(callback: CallbackQuery, state: FSMContext):
    """Select specific videos from playlist."""
    data = await state.get_data()
    total = data.get("playlist_count", 0)

    await safe_edit(callback.message,
        f"\U0001F522 <b>\u0412\u044b\u0431\u043e\u0440 \u0432\u0438\u0434\u0435\u043e</b>\n\n"
        f"\u0412\u0441\u0435\u0433\u043e \u0432 \u043f\u043b\u0435\u0439\u043b\u0438\u0441\u0442\u0435: {total}\n\n"
        "\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u043d\u043e\u043c\u0435\u0440\u0430 \u0432\u0438\u0434\u0435\u043e.\n"
        "\u041f\u0440\u0438\u043c\u0435\u0440\u044b:\n"
        "<code>1-10</code> \u2014 \u0432\u0438\u0434\u0435\u043e \u0441 1 \u043f\u043e 10\n"
        "<code>1,3,5,8</code> \u2014 \u043e\u0442\u0434\u0435\u043b\u044c\u043d\u044b\u0435 \u0432\u0438\u0434\u0435\u043e\n"
        "<code>1-5,10-15</code> \u2014 \u0434\u0438\u0430\u043f\u0430\u0437\u043e\u043d\u044b",
        reply_markup=cancel_kb(),
    )
    await state.set_state(PlaylistStates.waiting_for_range)
    await callback.answer()


@router.message(PlaylistStates.waiting_for_range)
async def process_range(message: Message, state: FSMContext):
    """Process user-entered range."""
    text = message.text.strip() if message.text else ""
    data = await state.get_data()
    total = data.get("playlist_count", 0)

    indices = parse_playlist_range(text, total)

    if not indices:
        await message.answer(
            f"\u274c \u041d\u0435\u043a\u043e\u0440\u0440\u0435\u043a\u0442\u043d\u044b\u0439 \u0432\u0432\u043e\u0434.\n"
            f"\u0414\u043e\u0441\u0442\u0443\u043f\u043d\u043e \u0432\u0438\u0434\u0435\u043e \u0441 1 \u043f\u043e {total}.\n"
            "\u041f\u0440\u0438\u043c\u0435\u0440: <code>1-10</code> \u0438\u043b\u0438 <code>1,3,5</code>",
            reply_markup=cancel_kb(),
        )
        return

    await state.update_data(selected_indices=indices)
    await message.answer(
        f"\u2705 \u0412\u044b\u0431\u0440\u0430\u043d\u043e \u0432\u0438\u0434\u0435\u043e: {len(indices)}\n"
        f"\u041d\u043e\u043c\u0435\u0440\u0430: {', '.join(str(i) for i in indices[:20])}"
        f"{'...' if len(indices) > 20 else ''}",
    )

    await _show_type_selection_message(message, state)


# === Type selection for playlist ===

async def _show_type_selection(callback: CallbackQuery, state: FSMContext):
    """Show media type selection for playlist."""
    await safe_edit(callback.message,
        "\U0001F3AC \u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0442\u0438\u043f:",
        reply_markup=playlist_type_kb(),
    )
    await state.set_state(PlaylistStates.selecting_type)


async def _show_type_selection_message(message: Message, state: FSMContext):
    """Show media type selection via message (not callback)."""
    await message.answer(
        "\U0001F3AC \u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0442\u0438\u043f:",
        reply_markup=playlist_type_kb(),
    )
    await state.set_state(PlaylistStates.selecting_type)


@router.callback_query(F.data == "pltype_video", PlaylistStates.selecting_type)
async def pl_type_video(callback: CallbackQuery, state: FSMContext):
    await state.update_data(media_type="video")
    await safe_edit(callback.message,
        "\U0001F4F1 \u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u043a\u0430\u0447\u0435\u0441\u0442\u0432\u043e:",
        reply_markup=playlist_quality_kb(),
    )
    await state.set_state(PlaylistStates.selecting_quality)
    await callback.answer()


@router.callback_query(F.data == "pltype_audio", PlaylistStates.selecting_type)
async def pl_type_audio(callback: CallbackQuery, state: FSMContext):
    await state.update_data(media_type="audio")
    await safe_edit(callback.message,
        "\U0001F3A7 \u041a\u0430\u0447\u0435\u0441\u0442\u0432\u043e \u0430\u0443\u0434\u0438\u043e:",
        reply_markup=playlist_audio_quality_kb(),
    )
    await state.set_state(PlaylistStates.selecting_quality)
    await callback.answer()


# === Quality selection ===

@router.callback_query(F.data.startswith("plq_"), PlaylistStates.selecting_quality)
async def pl_quality(callback: CallbackQuery, state: FSMContext):
    quality = callback.data.split("_", 1)[1]
    await state.update_data(quality=quality)

    data = await state.get_data()
    if data.get("media_type") == "video":
        await safe_edit(callback.message,
            f"\U0001F4F1 \u041a\u0430\u0447\u0435\u0441\u0442\u0432\u043e: {quality}\n\n\u0424\u043e\u0440\u043c\u0430\u0442:",
            reply_markup=playlist_format_kb(),
        )
    else:
        await safe_edit(callback.message,
            f"\U0001F3A7 \u041a\u0430\u0447\u0435\u0441\u0442\u0432\u043e: {quality}\n\n\u0424\u043e\u0440\u043c\u0430\u0442:",
            reply_markup=playlist_audio_format_kb(),
        )

    await state.set_state(PlaylistStates.selecting_format)
    await callback.answer()


@router.callback_query(F.data.startswith("plaq_"), PlaylistStates.selecting_quality)
async def pl_audio_quality(callback: CallbackQuery, state: FSMContext):
    quality = callback.data.split("_", 1)[1]
    await state.update_data(quality=quality)

    await safe_edit(callback.message,
        f"\U0001F3A7 \u041a\u0430\u0447\u0435\u0441\u0442\u0432\u043e: {quality} kbps\n\n\u0424\u043e\u0440\u043c\u0430\u0442:",
        reply_markup=playlist_audio_format_kb(),
    )
    await state.set_state(PlaylistStates.selecting_format)
    await callback.answer()


# === Format selection -> start download ===

@router.callback_query(F.data.startswith("plfmt_"), PlaylistStates.selecting_format)
async def pl_format(callback: CallbackQuery, state: FSMContext):
    fmt = callback.data.split("_", 1)[1]
    await state.update_data(format=fmt)
    await _start_playlist_download(callback, state)


@router.callback_query(F.data.startswith("plafmt_"), PlaylistStates.selecting_format)
async def pl_audio_format(callback: CallbackQuery, state: FSMContext):
    fmt = callback.data.split("_", 1)[1]
    await state.update_data(format=fmt)
    await _start_playlist_download(callback, state)


async def _start_playlist_download(callback: CallbackQuery, state: FSMContext):
    """Start downloading all selected playlist videos."""
    from services.download_service import download_service

    data = await state.get_data()
    entries = data.get("playlist_entries", [])
    indices = data.get("selected_indices", [])
    media_type = data.get("media_type", "video")
    quality = data.get("quality", "best")
    fmt = data.get("format", "mp4")

    await state.set_state(PlaylistStates.downloading)

    total = len(indices)
    _mt = "\u0412\u0438\u0434\u0435\u043e" if media_type == "video" else "\u0410\u0443\u0434\u0438\u043e"
    await safe_edit(callback.message,
        f"\U0001F4CB \u0417\u0430\u0433\u0440\u0443\u0437\u043a\u0430 \u043f\u043b\u0435\u0439\u043b\u0438\u0441\u0442\u0430\n\n"
        f"\u0412\u0441\u0435\u0433\u043e: {total} \u0432\u0438\u0434\u0435\u043e\n"
        f"\u0422\u0438\u043f: {_mt}\n"
        f"\u041a\u0430\u0447\u0435\u0441\u0442\u0432\u043e: {quality}\n"
        f"\u0424\u043e\u0440\u043c\u0430\u0442: {fmt.upper()}\n\n"
        "\u23f3 \u041e\u0436\u0438\u0434\u0430\u0439\u0442\u0435..."
    )
    await callback.answer()

    success_count = 0
    error_count = 0

    for idx in indices:
        if idx <= 0 or idx > len(entries):
            error_count += 1
            continue

        entry = entries[idx - 1]
        entry_url = entry.get("url", "")
        entry_title = entry.get("title", f"Video {idx}")

        try:
            task_id = await download_service.start_download(
                user_id=callback.from_user.id,
                chat_id=callback.message.chat.id,
                url=entry_url,
                media_type=media_type,
                quality=quality,
                fmt=fmt,
                title=entry_title,
                uploader=entry.get("uploader"),
                index=idx,
                total=total,
            )

            if task_id:
                # Wait for this task to complete before starting next
                from services.queue_service import download_queue
                task = download_queue.get_task(task_id)
                if task:
                    # Wait for completion (with timeout)
                    wait_count = 0
                    while task.status.value in ("pending", "downloading", "processing", "sending") and wait_count < 600:
                        await asyncio.sleep(2)
                        wait_count += 1

                    if task.status.value == "done":
                        success_count += 1
                    elif task.status.value in ("error", "cancelled"):
                        error_count += 1
            else:
                error_count += 1

        except Exception as e:
            logger.error("Playlist item %d failed: %s", idx, e)
            error_count += 1

    # Final report
    report = (
        f"\U0001F4CB \u041f\u043b\u0435\u0439\u043b\u0438\u0441\u0442 \u0437\u0430\u0432\u0435\u0440\u0448\u0451\u043d\n\n"
        f"\u0412\u0441\u0435\u0433\u043e: {total}\n"
        f"\u2705 \u0423\u0441\u043f\u0435\u0448\u043d\u043e: {success_count}\n"
        f"\u274c \u041e\u0448\u0438\u0431\u043e\u043a: {error_count}"
    )

    from bot.keyboards.main import main_menu_kb
    await callback.message.answer(report, reply_markup=main_menu_kb())
    await state.clear()


@router.callback_query(F.data == "cancel_playlist")
async def cancel_playlist(callback: CallbackQuery, state: FSMContext):
    """Cancel playlist download."""
    await state.clear()
    await safe_edit(callback.message,
        "\U0001F6AB \u0417\u0430\u0433\u0440\u0443\u0437\u043a\u0430 \u043f\u043b\u0435\u0439\u043b\u0438\u0441\u0442\u0430 \u043e\u0441\u0442\u0430\u043d\u043e\u0432\u043b\u0435\u043d\u0430.\n"
        "\u0423\u0436\u0435 \u0437\u0430\u0433\u0440\u0443\u0436\u0435\u043d\u043d\u044b\u0435 \u0444\u0430\u0439\u043b\u044b \u0441\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u044b.",
        reply_markup=back_to_main_kb(),
    )
    await callback.answer()
