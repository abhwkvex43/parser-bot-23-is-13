"""
yt-dlp wrapper for media parsing and extraction.

Provides async functions to:
- Extract media metadata without downloading
- Download video with quality/format selection
- Download audio with quality/format selection
- Download subtitles
- Get playlist information
"""
import asyncio
import logging
import os
from pathlib import Path
from typing import Any

import yt_dlp

from config import config
from utils.progress import DownloadProgress

logger = logging.getLogger(__name__)


DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


def _build_ydl_opts(
    *,
    progress: DownloadProgress | None = None,
    ffmpeg_path: str | None = None,
    extra_opts: dict | None = None,
) -> dict:
    """Build base yt-dlp options dict."""
    opts: dict[str, Any] = {
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "no_color": True,
        "restrictfilenames": False,
        "windowsfilenames": True,
        # Use bot's proxy for all yt-dlp network calls (Telegram API and yt-dlp share the same VPN)
        "proxy": config.PROXY_URL or None,
        # Retry transient SSL/network errors (common with VPN/proxy)
        "retries": 5,
        "fragment_retries": 5,
        "extractor_retries": 5,
        "file_access_retries": 3,
        # Network hardening: skip strict cert verification, force IPv4, longer timeouts
        "no_check_certificate": True,
        "source_address": "0.0.0.0",
        "socket_timeout": 30,
        # Present ourselves as a regular browser to avoid YouTube anti-bot detection
        "user_agent": DEFAULT_USER_AGENT,
        # Some videos only resolve via alternative clients; try them as fallback
        "extractor_args": {
            "youtube": {
                "player_client": ["web", "ios", "android", "tv"],
                "skip": ["translated_subs"],
            },
        },
    }
    # Drop None proxy to avoid yt-dlp falling back to env vars
    if not opts["proxy"]:
        opts.pop("proxy", None)
    if ffmpeg_path:
        opts["ffmpeg_location"] = ffmpeg_path
    if progress:
        opts["progress_hooks"] = [lambda d: _progress_hook(d, progress)]
    if extra_opts:
        opts.update(extra_opts)
    return opts


def _progress_hook(d: dict, progress: DownloadProgress) -> None:
    """Callback for yt-dlp download progress."""
    status = d.get("status", "")
    if status == "downloading":
        downloaded = d.get("downloaded_bytes", 0) or 0
        total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
        progress.update(downloaded, total)
    elif status == "finished":
        progress.status = "processing"
    elif status == "error":
        progress.status = "error"


def _run_sync(func, *args, **kwargs):
    """Run a synchronous yt-dlp function in a thread."""
    return asyncio.to_thread(func, *args, **kwargs)


async def extract_info(url: str, *, playlist: bool = False) -> dict:
    """Extract media metadata without downloading.

    Args:
        url: Media URL (video or playlist).
        playlist: If True, extract playlist entries.

    Returns:
        Dict with metadata (title, duration, uploader, formats, etc.)
    """
    opts = _build_ydl_opts()
    opts["noplaylist"] = not playlist
    opts["extract_flat"] = playlist  # Don't extract each video for playlist listing

    def _extract():
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=False)

    # Try primary strategy (with proxy + web client); fall back to alternative
    # strategies if the YouTube extractor fails (SSL, EOF, 403, etc.).
    strategies = [_extract]

    fallback_clients = [["ios"], ["android"], ["tv_embedded"]]
    for clients in fallback_clients:
        def _make_fallback(_clients=clients):
            alt_opts = dict(opts)
            alt_opts["extractor_args"] = {
                "youtube": {
                    "player_client": _clients,
                    "skip": ["translated_subs"],
                },
            }
            # Disable proxy as a last resort — direct connection sometimes works
            # when the VPN endpoint is the one being blocked.
            alt_opts["no_check_certificate"] = True
            def _do():
                with yt_dlp.YoutubeDL(alt_opts) as ydl:
                    return ydl.extract_info(url, download=False)
            return _do
        strategies.append(_make_fallback())

    last_error: Exception | None = None
    for attempt, fn in enumerate(strategies, start=1):
        try:
            info = await _run_sync(fn)
            if info:
                if attempt > 1:
                    logger.info("extract_info succeeded on attempt %d for %s", attempt, url)
                return info or {}
        except Exception as e:
            last_error = e
            logger.warning(
                "extract_info attempt %d failed for %s: %s",
                attempt, url, e,
            )
            # Don't retry on non-network errors
            err_text = str(e).lower()
            if "sign in" in err_text or "confirm your age" in err_text:
                raise

    logger.error("extract_info failed for %s after %d attempts", url, len(strategies))
    raise last_error or RuntimeError("extract_info failed")


async def extract_video_info(url: str) -> dict:
    """Extract metadata for a single video.

    Returns a simplified dict with:
        title, uploader, duration, thumbnail, formats (available qualities),
        subtitles (available languages), filesize_approx, is_live
    """
    raw = await extract_info(url, playlist=False)
    return _normalize_video_info(raw)


def _normalize_video_info(raw: dict) -> dict:
    """Convert raw yt-dlp info dict into a clean, UI-friendly structure."""
    # Available video qualities
    formats = raw.get("formats", [])
    video_qualities = set()
    for f in formats:
        if f.get("vbr") or f.get("height"):
            h = f.get("height")
            if h:
                video_qualities.add(f"{h}p")
    # Sort by height
    sorted_qualities = sorted(
        video_qualities,
        key=lambda q: int(q.rstrip("p")) if q.rstrip("p").isdigit() else 0
    )

    # Available subtitle languages
    subtitles = raw.get("subtitles", {})
    auto_subs = raw.get("automatic_captions", {})
    sub_langs = set()
    for lang in subtitles:
        sub_langs.add(lang)
    for lang in auto_subs:
        sub_langs.add(f"{lang} (auto)")

    # Approximate file size
    filesize = raw.get("filesize") or raw.get("filesize_approx")
    if not filesize and formats:
        # Find best format with filesize
        for f in reversed(formats):
            if f.get("filesize") or f.get("filesize_approx"):
                filesize = f.get("filesize") or f.get("filesize_approx")
                break

    return {
        "title": raw.get("title", "Unknown"),
        "uploader": raw.get("uploader") or raw.get("channel") or raw.get("uploader_id", "Unknown"),
        "duration": raw.get("duration", 0),
        "thumbnail": raw.get("thumbnail"),
        "url": raw.get("webpage_url") or raw.get("original_url", ""),
        "available_qualities": sorted_qualities,
        "subtitle_languages": sorted(sub_langs),
        "filesize_approx": filesize,
        "is_live": raw.get("is_live", False),
        "raw": raw,
    }


async def extract_playlist_info(url: str) -> dict:
    """Extract playlist metadata.

    Returns:
        Dict with title, entries (list of video dicts), total_count, total_duration
    """
    raw = await extract_info(url, playlist=True)
    entries = raw.get("entries", [])
    total_duration = sum(e.get("duration", 0) or 0 for e in entries if e)

    video_list = []
    for i, entry in enumerate(entries, 1):
        if not entry:
            continue
        video_list.append({
            "index": i,
            "title": entry.get("title", "Unknown"),
            "url": entry.get("url") or entry.get("webpage_url", ""),
            "duration": entry.get("duration", 0),
            "uploader": entry.get("uploader") or entry.get("channel", "Unknown"),
        })

    return {
        "title": raw.get("title", "Unknown Playlist"),
        "entries": video_list,
        "total_count": len(video_list),
        "total_duration": total_duration,
        "url": url,
    }


async def download_video(
    url: str,
    output_path: str,
    quality: str = "best",
    fmt: str = "mp4",
    progress: DownloadProgress | None = None,
    subtitle_lang: str | None = None,
    embed_subs: bool = False,
) -> Path:
    """Download a video with the specified quality and format.

    Args:
        url: Video URL.
        output_path: Output file template (without extension).
        quality: Quality string like "720p" or "best".
        fmt: Output format: mp4, mkv, webm.
        progress: Progress tracker.
        subtitle_lang: Subtitle language code (e.g. "ru", "en") or None.
        embed_subs: If True, embed subtitles into the video.

    Returns:
        Path to the downloaded file.
    """
    # Build format selector
    height = quality.rstrip("p") if quality != "best" else None
    if height and height.isdigit():
        fmt_selector = f"bestvideo[height<={height}]+bestaudio/best[height<={height}]/best"
    else:
        fmt_selector = "bestvideo+bestaudio/best"

    # Post-processing: merge to target format, embed subs
    postprocessors = []
    if fmt in ("mp4", "mkv", "webm"):
        postprocessors.append({
            "key": "FFmpegVideoConvertor",
            "preferedformat": fmt,
        })

    if embed_subs and subtitle_lang:
        postprocessors.append({
            "key": "FFmpegEmbedSubtitle",
        })
        sub_opts = {
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": [subtitle_lang, "en"],
            "subtitlesformat": "vtt/srt/best",
        }
    else:
        sub_opts = {}

    opts = _build_ydl_opts(
        progress=progress,
        ffmpeg_path=config.FFMPEG_PATH,
        extra_opts={
            "format": fmt_selector,
            "outtmpl": f"{output_path}.%(ext)s",
            "merge_output_format": fmt,
            "postprocessors": postprocessors,
            **sub_opts,
        },
    )

    def _download():
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

    await _run_sync(_download)

    # Find the actual output file
    result_path = _find_output_file(output_path, fmt)
    return result_path


async def download_audio(
    url: str,
    output_path: str,
    quality: str = "320",
    fmt: str = "mp3",
    progress: DownloadProgress | None = None,
) -> Path:
    """Download audio with the specified quality and format.

    Args:
        url: Video/audio URL.
        output_path: Output file template (without extension).
        quality: Bitrate string like "128", "192", "256", "320" or "best".
        fmt: Output format: mp3, m4a, opus, wav, flac.
        progress: Progress tracker.

    Returns:
        Path to the downloaded audio file.
    """
    # Audio format mapping
    audio_fmt_map = {
        "mp3": "mp3",
        "m4a": "m4a",
        "opus": "opus",
        "wav": "wav",
        "flac": "flac",
    }
    target = audio_fmt_map.get(fmt, "mp3")

    # Bitrate
    if quality != "best":
        bitrate_kbps = quality.lstrip("k").rstrip("kbps").strip()
        if bitrate_kbps.isdigit():
            postprocessor_quality = f"{bitrate_kbps}K"
        else:
            postprocessor_quality = "320K"
    else:
        postprocessor_quality = "0"  # 0 = best for mp3

    postprocessors = [{
        "key": "FFmpegExtractAudio",
        "preferredcodec": target,
        "preferredquality": postprocessor_quality if quality != "best" else "0",
    }]

    opts = _build_ydl_opts(
        progress=progress,
        ffmpeg_path=config.FFMPEG_PATH,
        extra_opts={
            "format": "bestaudio/best",
            "outtmpl": f"{output_path}.%(ext)s",
            "postprocessors": postprocessors,
        },
    )

    def _download():
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

    await _run_sync(_download)

    return _find_output_file(output_path, target)


async def download_subtitles(
    url: str,
    output_path: str,
    lang: str = "ru",
    fmt: str = "srt",
) -> Path | None:
    """Download subtitles only (no video, no audio).

    Args:
        url: Video URL.
        output_path: Output file template (without extension).
        lang: Subtitle language code.
        fmt: Subtitle format: srt, vtt, ass.

    Returns:
        Path to the subtitle file, or None if not available.
    """
    opts = _build_ydl_opts(
        ffmpeg_path=config.FFMPEG_PATH,
        extra_opts={
            "skip_download": True,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": [lang, "en"],
            "subtitlesformat": fmt,
            "outtmpl": f"{output_path}.%(ext)s",
        },
    )

    def _download():
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

    await _run_sync(_download)

    # Find the subtitle file
    for ext in (fmt, "srt", "vtt", "ass"):
        candidate = Path(f"{output_path}.{lang}.{ext}")
        if candidate.exists():
            return candidate
    return None


def _find_output_file(base_path: str, expected_ext: str) -> Path:
    """Find the actual output file after download.

    yt-dlp may produce files with various extensions; we look for the best match.
    """
    base = Path(base_path)
    parent = base.parent

    # Try exact expected extension first
    exact = Path(f"{base_path}.{expected_ext}")
    if exact.exists():
        return exact

    # Try any file starting with base name
    if parent.exists():
        candidates = sorted(
            parent.glob(f"{base.name}.*"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        for candidate in candidates:
            if candidate.suffix.lower() in (f".{expected_ext}", ".mp4", ".mkv", ".webm", ".mp3", ".m4a", ".opus", ".wav", ".flac"):
                return candidate

    # Fallback: return expected path even if file doesn't exist yet
    return exact
