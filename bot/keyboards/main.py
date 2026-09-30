"""
Main menu and navigation keyboards.
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_menu_kb() -> InlineKeyboardMarkup:
    """Main menu after /start."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="\U0001F4E5 Скачать", callback_data="download"),
            InlineKeyboardButton(text="\U0001F4CB Плейлист", callback_data="playlist"),
        ],
        [
            InlineKeyboardButton(text="\u2699\ufe0f Настройки", callback_data="settings"),
            InlineKeyboardButton(text="\u2753 Помощь", callback_data="help"),
        ],
        [
            InlineKeyboardButton(text="\U0001F4CA Мои загрузки", callback_data="my_downloads"),
        ],
        [
            InlineKeyboardButton(text="\U0001F4DD Авторы", callback_data="authors"),
        ],
    ])


def start_kb() -> InlineKeyboardMarkup:
    """Start screen keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="\U0001F4E5 Скачать медиа", callback_data="download"),
            InlineKeyboardButton(text="\U0001F4CB Плейлист", callback_data="playlist"),
        ],
        [
            InlineKeyboardButton(text="\u2699\ufe0f Настройки", callback_data="settings"),
            InlineKeyboardButton(text="\u2753 Помощь", callback_data="help"),
        ],
        [
            InlineKeyboardButton(text="\U0001F4DD Авторы", callback_data="authors"),
        ],
    ])


def back_to_main_kb() -> InlineKeyboardMarkup:
    """Back to main menu button."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\u2b05\ufe0f \u041d\u0430\u0437\u0430\u0434 \u0432 \u043c\u0435\u043d\u044e", callback_data="main_menu")],
    ])


def cancel_kb() -> InlineKeyboardMarkup:
    """Cancel button."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\u274c \u041e\u0442\u043c\u0435\u043d\u0438\u0442\u044c", callback_data="cancel_action")],
    ])


def media_type_kb() -> InlineKeyboardMarkup:
    """Choose media type (video/audio/subtitles)."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001F3AC \u0412\u0438\u0434\u0435\u043e", callback_data="type_video")],
        [InlineKeyboardButton(text="\U0001F3B5 \u0410\u0443\u0434\u0438\u043e", callback_data="type_audio")],
        [InlineKeyboardButton(text="\U0001F4DD \u0421\u0443\u0431\u0442\u0438\u0442\u0440\u044b", callback_data="type_subtitles")],
        [InlineKeyboardButton(text="\u274c \u041e\u0442\u043c\u0435\u043d\u0430", callback_data="cancel_action")],
    ])
