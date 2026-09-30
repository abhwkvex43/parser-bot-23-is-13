"""
Subtitle download module.
"""
import logging
from pathlib import Path

from config import config
from downloader.parser import download_subtitles
from utils.filenames import sanitize_filename

logger = logging.getLogger(__name__)


async def download(
    url: str,
    title: str,
    lang: str,
    fmt: str = "srt",
    user_id: int = 0,
) -> Path | None:
    """Download subtitle file only.

    Returns path to the subtitle file, or None if not available.
    """
    safe_name = sanitize_filename(title)
    output_template = str(config.TEMP_DIR / f"{user_id}_{safe_name}")

    file_path = await download_subtitles(
        url=url,
        output_path=output_template,
        lang=lang,
        fmt=fmt,
    )

    if file_path:
        logger.info("Subtitles downloaded: %s [%s] -> %s", url, lang, file_path)
    else:
        logger.warning("No subtitles found for %s [%s]", url, lang)

    return file_path
