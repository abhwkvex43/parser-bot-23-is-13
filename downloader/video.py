"""
Video download orchestration module.
"""
import logging
from pathlib import Path

from config import config
from downloader.parser import download_video, extract_video_info
from utils.filenames import format_filename, sanitize_filename
from utils.progress import DownloadProgress

logger = logging.getLogger(__name__)


async def get_video_info(url: str) -> dict:
    """Get video metadata for display."""
    info = await extract_video_info(url)
    logger.info("Video info extracted: %s — %s", url, info.get("title"))
    return info


async def download(
    url: str,
    title: str,
    uploader: str | None,
    quality: str,
    fmt: str,
    progress: DownloadProgress,
    subtitle_lang: str | None = None,
    embed_subs: bool = False,
    user_id: int = 0,
) -> Path:
    """Download a video file.

    Returns path to the downloaded file.
    """
    filename = format_filename(title, uploader, fmt)
    # Sanitize for temp storage
    safe_name = sanitize_filename(filename)
    output_template = str(config.TEMP_DIR / f"{user_id}_{safe_name}")

    file_path = await download_video(
        url=url,
        output_path=output_template,
        quality=quality,
        fmt=fmt,
        progress=progress,
        subtitle_lang=subtitle_lang,
        embed_subs=embed_subs,
    )

    logger.info("Video downloaded: %s -> %s", url, file_path)
    return file_path
