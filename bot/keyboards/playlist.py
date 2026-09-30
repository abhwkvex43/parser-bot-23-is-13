"""
Playlist selection keyboards.
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def playlist_action_kb() -> InlineKeyboardMarkup:
    """Choose playlist action."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001F4E5 \u0421\u043a\u0430\u0447\u0430\u0442\u044c \u0432\u0435\u0441\u044c \u043f\u043b\u0435\u0439\u043b\u0438\u0441\u0442", callback_data="pl_all")],
        [InlineKeyboardButton(text="\U0001F522 \u0412\u044b\u0431\u0440\u0430\u0442\u044c \u0432\u0438\u0434\u0435\u043e", callback_data="pl_select")],
        [InlineKeyboardButton(text="\u274c \u041e\u0442\u043c\u0435\u043d\u0430", callback_data="cancel_action")],
    ])


def playlist_type_kb() -> InlineKeyboardMarkup:
    """Choose media type for playlist download."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001F3AC \u0412\u0438\u0434\u0435\u043e", callback_data="pltype_video")],
        [InlineKeyboardButton(text="\U0001F3B5 \u0410\u0443\u0434\u0438\u043e", callback_data="pltype_audio")],
        [InlineKeyboardButton(text="\u274c \u041e\u0442\u043c\u0435\u043d\u0430", callback_data="cancel_action")],
    ])


def playlist_quality_kb() -> InlineKeyboardMarkup:
    """Choose quality for playlist download."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="360p", callback_data="plq_360p"),
            InlineKeyboardButton(text="480p", callback_data="plq_480p"),
        ],
        [
            InlineKeyboardButton(text="720p", callback_data="plq_720p"),
            InlineKeyboardButton(text="1080p", callback_data="plq_1080p"),
        ],
        [InlineKeyboardButton(text="\u041b\u0443\u0447\u0448\u0435\u0435", callback_data="plq_best")],
        [InlineKeyboardButton(text="\u274c \u041e\u0442\u043c\u0435\u043d\u0430", callback_data="cancel_action")],
    ])


def playlist_audio_quality_kb() -> InlineKeyboardMarkup:
    """Choose audio quality for playlist."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="128", callback_data="plaq_128"),
            InlineKeyboardButton(text="192", callback_data="plaq_192"),
        ],
        [
            InlineKeyboardButton(text="256", callback_data="plaq_256"),
            InlineKeyboardButton(text="320", callback_data="plaq_320"),
        ],
        [InlineKeyboardButton(text="\u041b\u0443\u0447\u0448\u0435\u0435", callback_data="plaq_best")],
        [InlineKeyboardButton(text="\u274c \u041e\u0442\u043c\u0435\u043d\u0430", callback_data="cancel_action")],
    ])


def playlist_format_kb() -> InlineKeyboardMarkup:
    """Choose format for playlist download."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="MP4", callback_data="plfmt_mp4"),
            InlineKeyboardButton(text="MKV", callback_data="plfmt_mkv"),
            InlineKeyboardButton(text="WEBM", callback_data="plfmt_webm"),
        ],
        [InlineKeyboardButton(text="\u274c \u041e\u0442\u043c\u0435\u043d\u0430", callback_data="cancel_action")],
    ])


def playlist_audio_format_kb() -> InlineKeyboardMarkup:
    """Choose audio format for playlist."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="MP3", callback_data="plafmt_mp3"),
            InlineKeyboardButton(text="M4A", callback_data="plafmt_m4a"),
            InlineKeyboardButton(text="OPUS", callback_data="plafmt_opus"),
        ],
        [InlineKeyboardButton(text="\u274c \u041e\u0442\u043c\u0435\u043d\u0430", callback_data="cancel_action")],
    ])


def cancel_playlist_kb() -> InlineKeyboardMarkup:
    """Cancel playlist download."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001F6AB \u041e\u0441\u0442\u0430\u043d\u043e\u0432\u0438\u0442\u044c \u043f\u043b\u0435\u0439\u043b\u0438\u0441\u0442", callback_data="cancel_playlist")],
    ])
