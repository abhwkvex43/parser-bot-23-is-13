"""
URL validation and media link type detection.
"""
import re
from urllib.parse import urlparse


# Regex patterns for known sources
YOUTUBE_VIDEO_PATTERNS = [
    re.compile(r'(youtube\.com/watch\?v=|youtu\.be/)', re.IGNORECASE),
]
YOUTUBE_PLAYLIST_PATTERNS = [
    re.compile(r'youtube\.com/playlist\?list=', re.IGNORECASE),
    re.compile(r'[?&]list=', re.IGNORECASE),
]
YOUTUBE_MUSIC_PATTERNS = [
    re.compile(r'music\.youtube\.com', re.IGNORECASE),
]

# General URL validation
URL_REGEX = re.compile(
    r'^https?://'            # scheme
    r'(?:\S+(?::\S*)?@)?'    # optional userinfo
    r'(?:'                   # host
    r'(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z]{2,})'  # domain
    r'|(?:\d{1,3}\.){3}\d{1,3}'                              # IPv4
    r')'
    r'(?::\d+)?'             # optional port
    r'(?:/[^\s]*)?'          # path
    r'$',
    re.IGNORECASE,
)


def is_valid_url(url: str) -> bool:
    """Check if a string is a valid HTTP(S) URL."""
    if not url or not isinstance(url, str):
        return False
    url = url.strip()
    return bool(URL_REGEX.match(url))


def detect_url_type(url: str) -> str:
    """Detect the type of media URL.

    Returns:
        "playlist"  — YouTube playlist link
        "music"     — YouTube Music link
        "video"     — Regular video link
        "unknown"   — Unrecognized URL
    """
    if not is_valid_url(url):
        return "unknown"

    url_lower = url.lower()

    # Check for playlist (check before video since playlist URLs may also contain video ID)
    for pattern in YOUTUBE_PLAYLIST_PATTERNS:
        if pattern.search(url_lower):
            return "playlist"

    # YouTube Music
    for pattern in YOUTUBE_MUSIC_PATTERNS:
        if pattern.search(url_lower):
            return "music"

    # YouTube video
    for pattern in YOUTUBE_VIDEO_PATTERNS:
        if pattern.search(url_lower):
            return "video"

    # Default: treat as video (yt-dlp will handle detection)
    return "video"


def parse_playlist_range(text: str, total: int) -> list[int] | None:
    """Parse a user-entered range string into a list of indices.

    Supports:
        "1-10"        → [1, 2, ..., 10]
        "1,3,5,8"     → [1, 3, 5, 8]
        "10-20"       → [10, 11, ..., 20]
        "1-5,8,10-12" → [1, 2, 3, 4, 5, 8, 10, 11, 12]

    Returns None if input is invalid.
    """
    text = text.strip()
    if not text:
        return None

    indices: set[int] = set()
    parts = text.split(",")

    for part in parts:
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            range_parts = part.split("-")
            if len(range_parts) != 2:
                return None
            try:
                start = int(range_parts[0].strip())
                end = int(range_parts[1].strip())
            except ValueError:
                return None
            if start < 1 or end < start or end > total:
                return None
            indices.update(range(start, end + 1))
        else:
            try:
                idx = int(part)
            except ValueError:
                return None
            if idx < 1 or idx > total:
                return None
            indices.add(idx)

    if not indices:
        return None

    return sorted(indices)
