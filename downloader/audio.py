"""
Audio download orchestration module.
"""
import logging
from pathlib import Path

from config import config
from downloader.parser import download_audio
from utils.filenames import format_filename, sanitize_filename
from utils.progress import DownloadProgress

logger = logging.getLogger(__name__)


async def download(
    url: str,
    title: str,
    uploader: str | None,
    quality: str,
    fmt: str,
    progress: DownloadProgress,
    user_id: int = 0,
) -> Path:
    """Download an audio file (extracted from video if needed).

    Returns path to the downloaded audio file.
    """
    filename = format_filename(title, uploader, fmt)
    safe_name = sanitize_filename(filename)
    output_template = str(config.TEMP_DIR / f"{user_id}_{safe_name}")

    file_path = await download_audio(
        url=url,
        output_path=output_template,
        quality=quality,
        fmt=fmt,
        progress=progress,
    )

    logger.info("Audio downloaded: %s -> %s", url, file_path)
    return file_path
