"""
Progress tracking and formatting for downloads.
"""
import time
from dataclasses import dataclass, field


@dataclass
class DownloadProgress:
    """Tracks download progress and calculates speed, ETA, etc."""

    total_bytes: int = 0
    downloaded_bytes: int = 0
    speed: float = 0.0         # bytes/sec
    eta: float = 0.0           # seconds
    status: str = "pending"    # pending | downloading | processing | done | error | cancelled
    started_at: float = field(default_factory=time.time)
    last_update: float = field(default_factory=time.time)
    last_sent: float = 0.0     # Last time progress was sent to Telegram
    _last_bytes: int = 0
    _last_time: float = field(default_factory=time.time)

    def update(self, downloaded_bytes: int, total_bytes: int) -> None:
        """Update progress from yt-dlp hook."""
        now = time.time()
        self.downloaded_bytes = downloaded_bytes
        if total_bytes and total_bytes > 0:
            self.total_bytes = total_bytes

        # Calculate speed
        dt = now - self._last_time
        if dt > 0:
            delta = downloaded_bytes - self._last_bytes
            self.speed = delta / dt
            if self.speed > 0 and self.total_bytes:
                remaining = self.total_bytes - downloaded_bytes
                self.eta = remaining / self.speed

        self._last_bytes = downloaded_bytes
        self._last_time = now
        self.last_update = now
        self.status = "downloading"

    @property
    def percent(self) -> float:
        """Completion percentage (0–100)."""
        if self.total_bytes <= 0:
            return 0.0
        return min(100.0, (self.downloaded_bytes / self.total_bytes) * 100)

    @property
    def should_send(self) -> bool:
        """Whether enough time has passed to send an update (throttle: 2 seconds)."""
        now = time.time()
        if now - self.last_sent >= 2.0:
            self.last_sent = now
            return True
        return False

    def format_bar(self, width: int = 20) -> str:
        """Format a text progress bar."""
        filled = int(width * self.percent / 100)
        return "\u2588" * filled + "\u2591" * (width - filled)

    @staticmethod
    def format_size(num_bytes: float) -> str:
        """Format bytes into human-readable string."""
        if num_bytes <= 0:
            return "0 B"
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if num_bytes < 1024:
                return f"{num_bytes:.1f} {unit}"
            num_bytes /= 1024
        return f"{num_bytes:.1f} PB"

    @staticmethod
    def format_speed(speed: float) -> str:
        """Format speed in human-readable form."""
        return f"{DownloadProgress.format_size(speed)}/s"

    @staticmethod
    def format_eta(seconds: float) -> str:
        """Format ETA as a human-readable duration."""
        if seconds <= 0:
            return "--"
        if seconds < 60:
            return f"{int(seconds)} sec"
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"

    def format_message(self) -> str:
        """Format the full progress message for Telegram."""
        pct = self.percent
        bar = self.format_bar()
        downloaded = self.format_size(self.downloaded_bytes)
        total = self.format_size(self.total_bytes)
        speed = self.format_speed(self.speed)
        eta = self.format_eta(self.eta)

        status_emoji = {
            "downloading": "\u2b07\ufe0f",
            "processing": "\u2699\ufe0f",
            "done": "\u2705",
            "error": "\u274c",
            "cancelled": "\U0001F6AB",
        }.get(self.status, "\u2b07\ufe0f")

        return (
            f"{status_emoji} \u0417\u0430\u0433\u0440\u0443\u0437\u043a\u0430\n\n"
            f"`{bar}` {pct:.0f}%\n\n"
            f"\u0420\u0430\u0437\u043c\u0435\u0440: {downloaded} / {total}\n"
            f"\u0421\u043a\u043e\u0440\u043e\u0441\u0442\u044c: {speed}\n"
            f"\u041e\u0441\u0442\u0430\u043b\u043e\u0441\u044c: {eta}"
        )


def format_duration(seconds: int | float) -> str:
    """Format seconds into HH:MM:SS or MM:SS string."""
    if not seconds or seconds < 0:
        return "--:--"
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def format_total_duration(seconds: int | float) -> str:
    """Format total duration as 'X h Y min' or 'Y min Z sec'."""
    if not seconds or seconds < 0:
        return "--"
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    if hours > 0:
        return f"{hours} \u0447 {minutes} \u043c\u0438\u043d"
    if minutes > 0:
        secs = seconds % 60
        return f"{minutes} \u043c\u0438\u043d {secs} \u0441\u0435\u043a"
    return f"{seconds} \u0441\u0435\u043a"
