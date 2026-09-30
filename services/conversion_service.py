"""
FFmpeg conversion service.
Handles post-download format conversion when yt-dlp can't produce the target format directly.
"""
import asyncio
import logging
import os
import shutil
from pathlib import Path

from config import config

logger = logging.getLogger(__name__)


async def convert_video(input_path: Path, target_format: str) -> Path:
    """Convert a video file to a different format using FFmpeg.

    Args:
        input_path: Source video file.
        target_format: Target format (mp4, mkv, webm).

    Returns:
        Path to the converted file.
    """
    target_format = target_format.lower().lstrip(".")
    output_path = input_path.with_suffix(f".{target_format}")

    if output_path == input_path:
        return input_path

    cmd = [
        config.FFMPEG_PATH, "-y",
        "-i", str(input_path),
        "-c:v", "copy",
        "-c:a", "copy",
        str(output_path),
    ]

    logger.info("Converting video: %s -> %s", input_path, output_path)

    def _run():
        return asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

    proc = await _run()
    _, stderr = await proc.communicate()

    if proc.returncode != 0:
        err = stderr.decode(errors="replace")[-500:] if stderr else "Unknown error"
        # If copy fails, try re-encoding
        logger.warning("Direct copy failed, re-encoding: %s", err)
        cmd_reencode = [
            config.FFMPEG_PATH, "-y",
            "-i", str(input_path),
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "aac",
            str(output_path),
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd_reencode,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            err = stderr.decode(errors="replace")[-500:] if stderr else "Unknown error"
            logger.error("FFmpeg conversion failed: %s", err)
            raise RuntimeError(f"FFmpeg conversion failed: {err}")

    # Clean up original if different from output
    if output_path != input_path and input_path.exists():
        try:
            os.remove(str(input_path))
        except SystemExit:
            pass
        except Exception as e:
            logger.warning("Failed to clean up %s: %s", input_path, e)

    return output_path


async def convert_audio(input_path: Path, target_format: str, bitrate: str = "320k") -> Path:
    """Convert an audio file to a different format.

    Args:
        input_path: Source audio file.
        target_format: Target format (mp3, m4a, opus, wav, flac).
        bitrate: Target bitrate for lossy formats.

    Returns:
        Path to the converted file.
    """
    target_format = target_format.lower().lstrip(".")
    output_path = input_path.with_suffix(f".{target_format}")

    if output_path == input_path:
        return input_path

    codec_map = {
        "mp3": ("libmp3lame", None),
        "m4a": ("aac", None),
        "opus": ("libopus", None),
        "wav": ("pcm_s16le", None),
        "flac": ("flac", None),
    }

    audio_codec, _ = codec_map.get(target_format, ("libmp3lame", None))

    cmd = [config.FFMPEG_PATH, "-y", "-i", str(input_path)]

    if audio_codec:
        cmd.extend(["-c:a", audio_codec])
    if target_format in ("mp3", "m4a", "opus"):
        cmd.extend(["-b:a", bitrate])
    cmd.append(str(output_path))

    logger.info("Converting audio: %s -> %s", input_path, output_path)

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()

    if proc.returncode != 0:
        err = stderr.decode(errors="replace")[-500:] if stderr else "Unknown error"
        logger.error("Audio conversion failed: %s", err)
        raise RuntimeError(f"Audio conversion failed: {err}")

    if output_path != input_path and input_path.exists():
        try:
            os.remove(str(input_path))
        except SystemExit:
            pass
        except Exception as e:
            logger.warning("Failed to clean up %s: %s", input_path, e)

    return output_path


def get_file_size_mb(path: Path) -> float:
    """Get file size in megabytes."""
    if not path.exists():
        return 0.0
    return path.stat().st_size / (1024 * 1024)
