"""
Quality selection keyboards.
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def video_quality_kb(available: list[str] | None = None) -> InlineKeyboardMarkup:
    """Choose video quality.

    Args:
        available: List of available qualities (e.g. ["360p", "720p", "1080p"]).
                   If None, shows all standard options.
    """
    all_qualities = ["360p", "480p", "720p", "1080p"]

    if available:
        # Filter to available, but always include "best"
        qualities = [q for q in all_qualities if q in available]
    else:
        qualities = all_qualities

    rows = []
    for q in qualities:
        rows.append([InlineKeyboardButton(text=f"\U0001F539 {q}", callback_data=f"vq_{q}")])

    rows.append([InlineKeyboardButton(text="\U0001F539 \u041b\u0443\u0447\u0448\u0435\u0435 \u0434\u043e\u0441\u0442\u0443\u043f\u043d\u043e\u0435", callback_data="vq_best")])
    rows.append([InlineKeyboardButton(text="\u274c \u041e\u0442\u043c\u0435\u043d\u0430", callback_data="cancel_action")])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def audio_quality_kb() -> InlineKeyboardMarkup:
    """Choose audio quality (bitrate)."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="128 kbps", callback_data="aq_128"),
            InlineKeyboardButton(text="192 kbps", callback_data="aq_192"),
        ],
        [
            InlineKeyboardButton(text="256 kbps", callback_data="aq_256"),
            InlineKeyboardButton(text="320 kbps", callback_data="aq_320"),
        ],
        [InlineKeyboardButton(text="\U0001F539 \u041b\u0443\u0447\u0448\u0435\u0435 \u0434\u043e\u0441\u0442\u0443\u043f\u043d\u043e\u0435", callback_data="aq_best")],
        [InlineKeyboardButton(text="\u274c \u041e\u0442\u043c\u0435\u043d\u0430", callback_data="cancel_action")],
    ])


def subtitle_lang_kb(available_langs: list[str] | None = None) -> InlineKeyboardMarkup:
    """Choose subtitle language.

    Args:
        available_langs: List of available language codes.
    """
    common_langs = [
        ("ru", "\U0001F1F7\U0001F1FA \u0420\u0443\u0441\u0441\u043a\u0438\u0439"),
        ("en", "\U0001F1EC\U0001F1E7 English"),
        ("de", "\U0001F1E9\U0001F1EA Deutsch"),
        ("it", "\U0001F1EE\U0001F1F9 Italiano"),
        ("fr", "\U0001F1EB\U0001F1F7 Fran\u00e7ais"),
        ("es", "\U0001F1EA\U0001F1F8 Espa\u00f1ol"),
        ("pt", "\U0001F1F5\U0001F1F9 Portugu\u00eas"),
        ("ja", "\U0001F1EF\U0001F1F5 \u65e5\u672c\u8a9e"),
    ]

    rows = []
    for code, label in common_langs:
        if not available_langs or code in available_langs or any(code in l for l in available_langs):
            rows.append([InlineKeyboardButton(text=label, callback_data=f"slang_{code}")])

    rows.append([InlineKeyboardButton(text="\u274c \u0411\u0435\u0437 \u0441\u0443\u0431\u0442\u0438\u0442\u0440\u043e\u0432", callback_data="slang_none")])
    rows.append([InlineKeyboardButton(text="\u274c \u041e\u0442\u043c\u0435\u043d\u0430", callback_data="cancel_action")])

    return InlineKeyboardMarkup(inline_keyboard=rows)
