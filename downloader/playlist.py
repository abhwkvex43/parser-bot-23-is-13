"""
Playlist handling module.
"""
import logging
from dataclasses import dataclass

from downloader.parser import extract_playlist_info

logger = logging.getLogger(__name__)


@dataclass
class PlaylistVideo:
    """Represents a single video in a playlist."""
    index: int
    title: str
    url: str
    duration: int
    uploader: str


async def get_playlist_info(url: str) -> dict:
    """Get playlist metadata for display.

    Returns dict with:
        title, entries (list), total_count, total_duration, url
    """
    info = await extract_playlist_info(url)
    logger.info(
        "Playlist info: %s — %d videos, %d sec total",
        info.get("title"),
        info.get("total_count"),
        info.get("total_duration"),
    )
    return info


def select_videos(entries: list[dict], indices: list[int]) -> list[PlaylistVideo]:
    """Select a subset of playlist videos by index.

    Args:
        entries: Full list of playlist entry dicts.
        indices: 1-based indices to select.

    Returns:
        List of PlaylistVideo objects.
    """
    selected = []
    for idx in indices:
        if 1 <= idx <= len(entries):
            entry = entries[idx - 1]
            selected.append(PlaylistVideo(
                index=idx,
                title=entry.get("title", "Unknown"),
                url=entry.get("url", ""),
                duration=entry.get("duration", 0),
                uploader=entry.get("uploader", "Unknown"),
            ))
    return selected
