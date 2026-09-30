"""
Start command handler.
"""
import logging

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command

from database import database as db
from utils.safe_edit import safe_edit
from bot.keyboards.main import start_kb, main_menu_kb, back_to_main_kb

logger = logging.getLogger(__name__)

router = Router()

AUTHORS_TEXT = (
    "\U0001F4DD Авторы проекта\n\n"
    "Группа 23-ИС-13\n\n"
    "Усов Михаил\n"
    "Димитриев Костя\n"
    "Антонов Савелий\n"
    "Данилов Антон\n"
    "Карташов Роберт"
)


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Handle /start command."""
    user = await db.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
    )
    logger.info("User started: %s (@%s)", message.from_user.id, message.from_user.username)

    welcome = (
        "\U0001F44B Привет! Я Парсер 23-ИС-13.\n\n"
        "Отправь мне ссылку на видео, аудио или плейлист, "
        "чтобы начать загрузку.\n\n"
        "\U0001F4CC Я автоматически определяю тип ссылки "
        "и предлагаю доступные варианты."
    )

    await message.answer(welcome, reply_markup=start_kb())


@router.callback_query(F.data == "main_menu")
async def cb_main_menu(callback: CallbackQuery):
    """Back to main menu."""
    text = (
        "\U0001F3E0 Главное меню\n\n"
        "Выберите действие:"
    )
    await safe_edit(callback.message, text, reply_markup=main_menu_kb())
    await callback.answer()


@router.callback_query(F.data == "authors")
async def cb_authors(callback: CallbackQuery):
    """Show authors."""
    await safe_edit(callback.message, AUTHORS_TEXT, reply_markup=back_to_main_kb())
    await callback.answer()
