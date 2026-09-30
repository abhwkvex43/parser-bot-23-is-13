"""
FSM states for the download flow.
"""
from aiogram.fsm.state import State, StatesGroup


class DownloadStates(StatesGroup):
    """States for the download flow."""
    waiting_for_url = State()
    analyzing = State()
    selecting_type = State()         # video | audio | subtitles
    selecting_video_quality = State()
    selecting_video_format = State()
    selecting_audio_quality = State()
    selecting_audio_format = State()
    selecting_subtitle_lang = State()
    selecting_subtitle_mode = State()  # separate file or embed
    selecting_subtitle_format = State()
    confirming = State()
    downloading = State()


class PlaylistStates(StatesGroup):
    """States for the playlist download flow."""
    waiting_for_url = State()
    analyzing = State()
    selecting_action = State()       # all | select range | cancel
    waiting_for_range = State()
    selecting_type = State()         # video | audio
    selecting_quality = State()
    selecting_format = State()
    selecting_subtitle_lang = State()
    downloading = State()


class SettingsStates(StatesGroup):
    """States for settings editing."""
    editing = State()
