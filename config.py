"""
Configuration module.
Loads settings from environment variables and .env file.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def _parse_admin_ids(raw: str) -> list[int]:
    """Parse comma-separated admin IDs from env."""
    if not raw:
        return []
    return [int(x.strip()) for x in raw.split(",") if x.strip().isdigit()]


def _find_ffmpeg() -> str:
    """Return FFmpeg executable path."""
    env_path = os.getenv("FFMPEG_PATH", "").strip()
    if env_path:
        return env_path
    # Check for local ffmpeg directory (downloaded bundle)
    local_dir = Path(__file__).parent / "ffmpeg"
    if local_dir.exists():
        bins = list(local_dir.glob("*/bin/ffmpeg.exe")) or list(local_dir.glob("*/bin/ffmpeg"))
        if bins:
            return str(bins[0])
    return "ffmpeg"


class Config:
    """Application configuration loaded from environment."""

    # Telegram
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    PROXY_URL: str = os.getenv("PROXY_URL", "")  # e.g. http://127.0.0.1:12334

    # Local Bot API server (raises upload/download limit to 2 GB)
    API_ID: str = os.getenv("API_ID", "")            # from https://my.telegram.org
    API_HASH: str = os.getenv("API_HASH", "")        # from https://my.telegram.org
    USE_LOCAL_BOT_API: bool = os.getenv("USE_LOCAL_BOT_API", "false").lower() in ("1", "true", "yes", "on")
    LOCAL_BOT_API_URL: str = os.getenv("LOCAL_BOT_API_URL", "http://127.0.0.1:8081")
    LOCAL_BOT_API_DIR: str = os.getenv("LOCAL_BOT_API_DIR", str(Path(__file__).parent / "telegram-bot-api-data"))

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/media_bot.db")

    # Directories
    DOWNLOAD_DIR: Path = Path(os.getenv("DOWNLOAD_DIR", "./downloads"))
    TEMP_DIR: Path = Path(os.getenv("TEMP_DIR", "./temp"))
    DATA_DIR: Path = Path("./data")
    LOG_DIR: Path = Path("./logs")

    # Limits
    MAX_CONCURRENT_DOWNLOADS: int = int(os.getenv("MAX_CONCURRENT_DOWNLOADS", "2"))
    MAX_USER_QUEUE: int = int(os.getenv("MAX_USER_QUEUE", "20"))
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "2048"))
    # Cloud Bot API caps files at 50 MB; local server allows up to 2000 MB.
    # Auto-detect: local API only works when API_ID and API_HASH are set.
    _env_local: bool = os.getenv("USE_LOCAL_BOT_API", "false").lower() in ("1", "true", "yes", "on")
    _has_creds: bool = bool(os.getenv("API_ID", "").strip() and os.getenv("API_HASH", "").strip())
    _effective_local: bool = _env_local and _has_creds
    TELEGRAM_FILE_LIMIT_MB: int = int(os.getenv("TELEGRAM_FILE_LIMIT_MB", "2000" if _effective_local else "50"))

    # Admins
    ADMIN_IDS: list[int] = _parse_admin_ids(os.getenv("ADMIN_IDS", ""))

    # FFmpeg
    FFMPEG_PATH: str = _find_ffmpeg()

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/bot.log")

    # Cleanup
    TEMP_FILE_TTL_HOURS: int = 1  # Auto-delete temp files older than 1 hour

    def ensure_dirs(self) -> None:
        """Create all required directories."""
        for d in (self.DOWNLOAD_DIR, self.TEMP_DIR, self.DATA_DIR, self.LOG_DIR):
            d.mkdir(parents=True, exist_ok=True)

    @property
    def telegram_file_limit_bytes(self) -> int:
        """Telegram Bot API file size limit in bytes (50 MB for standard bots)."""
        return self.TELEGRAM_FILE_LIMIT_MB * 1024 * 1024

    def is_admin(self, telegram_id: int) -> bool:
        """Check if a Telegram user is an admin."""
        return telegram_id in self.ADMIN_IDS


config = Config()
