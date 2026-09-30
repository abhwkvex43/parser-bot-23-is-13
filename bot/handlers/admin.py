"""
Admin handler — statistics, active downloads, disk usage.
"""
import logging
import shutil

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from config import config
from database import database as db
from services.queue_service import download_queue, TaskStatus
from utils.safe_edit import safe_edit
from bot.keyboards.main import back_to_main_kb

logger = logging.getLogger(__name__)

router = Router()


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Admin panel (admins only)."""
    if not config.is_admin(message.from_user.id):
        await message.answer("\u274c \u0423 \u0432\u0430\u0441 \u043d\u0435\u0442 \u043f\u0440\u0430\u0432 \u0430\u0434\u043c\u0438\u043d\u0438\u0441\u0442\u0440\u0430\u0442\u043e\u0440\u0430.")
        return

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001F465 \u041f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u0438", callback_data="admin_users")],
        [InlineKeyboardButton(text="\U0001F4E5 \u0410\u043a\u0442\u0438\u0432\u043d\u044b\u0435 \u0437\u0430\u0433\u0440\u0443\u0437\u043a\u0438", callback_data="admin_active")],
        [InlineKeyboardButton(text="\U0001F4CA \u0421\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u043a\u0430", callback_data="admin_stats")],
        [InlineKeyboardButton(text="\U0001F4BE \u0418\u0441\u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u043d\u0438\u0435 \u0434\u0438\u0441\u043a\u0430", callback_data="admin_disk")],
        [InlineKeyboardButton(text="\U0001F6D1 \u041e\u0441\u0442\u0430\u043d\u043e\u0432\u0438\u0442\u044c \u0437\u0430\u0433\u0440\u0443\u0437\u043a\u0438", callback_data="admin_stop_all")],
    ])

    await message.answer("\U0001F511 <b>\u0410\u0434\u043c\u0438\u043d-\u043f\u0430\u043d\u0435\u043b\u044c</b>", reply_markup=kb)


@router.callback_query(F.data.startswith("admin_"))
async def admin_actions(callback: CallbackQuery):
    """Handle admin panel actions."""
    if not config.is_admin(callback.from_user.id):
        await callback.answer("\u274c \u041d\u0435\u0442 \u043f\u0440\u0430\u0432", show_alert=True)
        return

    action = callback.data

    if action == "admin_stats":
        stats = await db.get_today_downloads_stats()
        users_count = await db.get_all_users_count()

        text = (
            "\U0001F4CA <b>\u0421\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u043a\u0430</b>\n\n"
            f"\u041f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u0435\u0439: {users_count}\n\n"
            f"\u0417\u0430\u0433\u0440\u0443\u0437\u043e\u043a \u0441\u0435\u0433\u043e\u0434\u043d\u044f: {stats['total']}\n"
            f"\u0412\u0438\u0434\u0435\u043e: {stats['video']}\n"
            f"\u0410\u0443\u0434\u0438\u043e: {stats['audio']}\n\n"
            f"\u0423\u0441\u043f\u0435\u0448\u043d\u043e: {stats['success']}\n"
            f"\u041e\u0448\u0438\u0431\u043e\u043a: {stats['errors']}"
        )

    elif action == "admin_active":
        active = download_queue.get_active_tasks()
        if not active:
            text = "\U0001F4E5 <b>\u0410\u043a\u0442\u0438\u0432\u043d\u044b\u0435 \u0437\u0430\u0433\u0440\u0443\u0437\u043a\u0438</b>\n\n\u041d\u0435\u0442 \u0430\u043a\u0442\u0438\u0432\u043d\u044b\u0445 \u0437\u0430\u0433\u0440\u0443\u0437\u043e\u043a."
        else:
            lines = ["\U0001F4E5 <b>\u0410\u043a\u0442\u0438\u0432\u043d\u044b\u0435 \u0437\u0430\u0433\u0440\u0443\u0437\u043a\u0438</b>\n"]
            for t in active[:20]:
                status_emoji = {
                    TaskStatus.DOWNLOADING: "\U0001F504",
                    TaskStatus.PROCESSING: "\u2699\ufe0f",
                    TaskStatus.SENDING: "\U0001F4E4",
                }.get(t.status, "\u23f3")
                title = (t.title or "Unknown")[:40]
                lines.append(f"{status_emoji} {title}")
            text = "\n".join(lines)

    elif action == "admin_disk":
        # Disk usage of temp and download dirs
        temp_size = _dir_size_mb(config.TEMP_DIR)
        download_size = _dir_size_mb(config.DOWNLOAD_DIR)
        disk_free = shutil.disk_usage(str(config.TEMP_DIR)).free / (1024 ** 3)

        text = (
            "\U0001F4BE <b>\u0418\u0441\u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u043d\u0438\u0435 \u0434\u0438\u0441\u043a\u0430</b>\n\n"
            f"\U0001F4E6 \u0412\u0440\u0435\u043c\u0435\u043d\u043d\u044b\u0435 \u0444\u0430\u0439\u043b\u044b: {temp_size:.1f} MB\n"
            f"\U0001F4E5 \u0417\u0430\u0433\u0440\u0443\u0437\u043a\u0438: {download_size:.1f} MB\n"
            f"\U0001F4BE \u0421\u0432\u043e\u0431\u043e\u0434\u043d\u043e: {disk_free:.1f} GB"
        )

    elif action == "admin_stop_all":
        active = download_queue.get_active_tasks()
        for t in active:
            await download_queue.cancel_task(t.task_id)
        text = f"\U0001F6D1 \u041e\u0441\u0442\u0430\u043d\u043e\u0432\u043b\u0435\u043d\u043e \u0437\u0430\u0433\u0440\u0443\u0437\u043e\u043a: {len(active)}"

    elif action == "admin_users":
        users_count = await db.get_all_users_count()
        text = f"\U0001F465 <b>\u041f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u0438</b>\n\n\u0412\u0441\u0435\u0433\u043e: {users_count}"

    else:
        text = "\u041d\u0435\u0438\u0437\u0432\u0435\u0441\u0442\u043d\u0430\u044f \u043a\u043e\u043c\u0430\u043d\u0434\u0430."

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\u2b05\ufe0f \u041d\u0430\u0437\u0430\u0434 \u0432 \u0430\u0434\u043c\u0438\u043d-\u043f\u0430\u043d\u0435\u043b\u044c", callback_data="admin_back")],
    ])

    if callback.data == "admin_back":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="\U0001F465 \u041f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u0438", callback_data="admin_users")],
            [InlineKeyboardButton(text="\U0001F4E5 \u0410\u043a\u0442\u0438\u0432\u043d\u044b\u0435 \u0437\u0430\u0433\u0440\u0443\u0437\u043a\u0438", callback_data="admin_active")],
            [InlineKeyboardButton(text="\U0001F4CA \u0421\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u043a\u0430", callback_data="admin_stats")],
            [InlineKeyboardButton(text="\U0001F4BE \u0418\u0441\u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u043d\u0438\u0435 \u0434\u0438\u0441\u043a\u0430", callback_data="admin_disk")],
            [InlineKeyboardButton(text="\U0001F6D1 \u041e\u0441\u0442\u0430\u043d\u043e\u0432\u0438\u0442\u044c \u0437\u0430\u0433\u0440\u0443\u0437\u043a\u0438", callback_data="admin_stop_all")],
        ])
        text = "\U0001F511 <b>\u0410\u0434\u043c\u0438\u043d-\u043f\u0430\u043d\u0435\u043b\u044c</b>"

    await safe_edit(callback.message,text, reply_markup=kb)
    await callback.answer()


def _dir_size_mb(path) -> float:
    """Calculate directory size in MB."""
    total = 0
    try:
        for f in path.rglob("*"):
            if f.is_file():
                total += f.stat().st_size
    except Exception:
        pass
    return total / (1024 * 1024)
