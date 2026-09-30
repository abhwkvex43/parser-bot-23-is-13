"""
Format selection keyboards.
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def video_format_kb(quality: str = "720p") -> InlineKeyboardMarkup:
    """Choose video format."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="MP4", callback_data=f"vfmt_mp4_{quality}"),
            InlineKeyboardButton(text="MKV", callback_data=f"vfmt_mkv_{quality}"),
            InlineKeyboardButton(text="WEBM", callback_data=f"vfmt_webm_{quality}"),
        ],
        [InlineKeyboardButton(text="\u2b05\ufe0f \u041d\u0430\u0437\u0430\u0434", callback_data="back_to_quality")],
        [InlineKeyboardButton(text="\u274c \u041e\u0442\u043c\u0435\u043d\u0430", callback_data="cancel_action")],
    ])


def audio_format_kb(quality: str = "320") -> InlineKeyboardMarkup:
    """Choose audio format."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="MP3", callback_data=f"afmt_mp3_{quality}"),
            InlineKeyboardButton(text="M4A", callback_data=f"afmt_m4a_{quality}"),
            InlineKeyboardButton(text="OPUS", callback_data=f"afmt_opus_{quality}"),
        ],
        [
            InlineKeyboardButton(text="WAV", callback_data=f"afmt_wav_{quality}"),
            InlineKeyboardButton(text="FLAC", callback_data=f"afmt_flac_{quality}"),
        ],
        [InlineKeyboardButton(text="\u2b05\ufe0f \u041d\u0430\u0437\u0430\u0434", callback_data="back_to_audio_quality")],
        [InlineKeyboardButton(text="\u274c \u041e\u0442\u043c\u0435\u043d\u0430", callback_data="cancel_action")],
    ])


def subtitle_format_kb() -> InlineKeyboardMarkup:
    """Choose subtitle format."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="SRT", callback_data="sfmt_srt"),
            InlineKeyboardButton(text="VTT", callback_data="sfmt_vtt"),
            InlineKeyboardButton(text="ASS", callback_data="sfmt_ass"),
        ],
        [InlineKeyboardButton(text="\u274c \u041e\u0442\u043c\u0435\u043d\u0430", callback_data="cancel_action")],
    ])


def subtitle_mode_kb() -> InlineKeyboardMarkup:
    """Choose subtitle mode: separate file or embedded."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="\U0001F4C4 \u041e\u0442\u0434\u0435\u043b\u044c\u043d\u044b\u0439 \u0444\u0430\u0439\u043b", callback_data="smode_separate"),
            InlineKeyboardButton(text="\U0001F4DD \u0412\u0448\u0438\u0442\u044c \u0432 \u0432\u0438\u0434\u0435\u043e", callback_data="smode_embed"),
        ],
        [InlineKeyboardButton(text="\u274c \u041e\u0442\u043c\u0435\u043d\u0430", callback_data="cancel_action")],
    ])
