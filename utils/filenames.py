"""
Filename sanitization and formatting utilities.
"""
import re
import unicodedata

# Characters that are invalid in Windows filenames
_INVALID_CHARS = re.compile(r'[\\/:*?"<>|]')
# Control characters and null bytes
_CONTROL_CHARS = re.compile(r'[\x00-\x1f]')
# Max filename length (excluding extension) — Windows limit is 255, we leave margin
MAX_NAME_LENGTH = 200


def sanitize_filename(name: str) -> str:
    """Sanitize a string for safe use as a filename.

    Replaces invalid filesystem characters with underscores,
    strips control characters, collapses whitespace.
    """
    if not name:
        return "media"

    # Replace invalid characters
    name = _INVALID_CHARS.sub("_", name)
    # Remove control characters
    name = _CONTROL_CHARS.sub("", name)
    # Strip leading/trailing whitespace and dots
    name = name.strip(". ")
    # Collapse multiple spaces/underscores
    name = re.sub(r'[\s_]+', " ", name).strip()
    # Truncate
    if len(name) > MAX_NAME_LENGTH:
        name = name[:MAX_NAME_LENGTH].rsplit(" ", 1)[0]
    return name if name else "media"


def format_filename(
    title: str,
    artist: str | None = None,
    ext: str = "mp4",
    index: int | None = None,
    total: int | None = None,
) -> str:
    """Build a clean, human-readable filename.

    Examples:
        "Artist - Title.mp4"
        "Title.mp4"
        "01 - Title.mp4"
    """
    title = sanitize_filename(title)
    artist = sanitize_filename(artist) if artist else None

    parts = []
    if index is not None:
        # Zero-pad index based on total
        pad = len(str(total)) if total else 2
        parts.append(f"{index:0{pad}d}")
    if artist:
        parts.append(artist)
    parts.append(title)

    filename = " - ".join(parts)
    ext = ext.lstrip(".").lower()
    return f"{filename}.{ext}"


def truncate_filename(filename: str, max_len: int = 64) -> str:
    """Truncate a filename (with extension) to fit within max_len characters."""
    if len(filename) <= max_len:
        return filename
    # Preserve extension
    if "." in filename:
        name, ext = filename.rsplit(".", 1)
        return f"{name[:max_len - len(ext) - 1]}.{ext}"
    return filename[:max_len]
