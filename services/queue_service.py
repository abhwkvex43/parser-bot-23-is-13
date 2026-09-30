"""
Async download queue service.
Manages concurrent download tasks with per-user and global limits.
"""
import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Any

from config import config

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    SENDING = "sending"
    DONE = "done"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass
class DownloadTask:
    """Represents a single download task in the queue."""
    task_id: str
    user_id: int
    url: str
    title: str = ""
    media_type: str = "video"       # video | audio | subtitles
    quality: str = "best"
    format: str = "mp4"
    subtitle_lang: str | None = None
    embed_subs: bool = False
    status: TaskStatus = TaskStatus.PENDING
    progress_text: str = ""
    error: str = ""
    result_file: str = ""
    file_size_mb: float = 0.0
    # Internal
    _cancel_event: asyncio.Event = field(default_factory=asyncio.Event, repr=False)
    _task: asyncio.Task | None = field(default=None, repr=False)
    playlist_id: str | None = None  # If part of a playlist download
    index: int | None = None        # Playlist item index
    total: int | None = None        # Playlist total

    def cancel(self):
        """Mark this task for cancellation."""
        self._cancel_event.set()

    @property
    def is_cancelled(self) -> bool:
        return self._cancel_event.is_set()


class DownloadQueue:
    """Manages a queue of download tasks with concurrency limits."""

    def __init__(self):
        self._tasks: dict[str, DownloadTask] = {}
        self._user_tasks: dict[int, list[str]] = {}
        self._global_semaphore = asyncio.Semaphore(config.MAX_CONCURRENT_DOWNLOADS)
        self._user_semaphores: dict[int, asyncio.Semaphore] = {}
        self._lock = asyncio.Lock()

    def _get_user_semaphore(self, user_id: int) -> asyncio.Semaphore:
        """Get or create a per-user semaphore (1 concurrent download per user)."""
        if user_id not in self._user_semaphores:
            self._user_semaphores[user_id] = asyncio.Semaphore(1)
        return self._user_semaphores[user_id]

    async def add_task(self, task: DownloadTask) -> str:
        """Add a task to the queue and start processing."""
        async with self._lock:
            # Check user queue limit
            user_active = [
                tid for tid in self._user_tasks.get(task.user_id, [])
                if self._tasks.get(tid) and self._tasks[tid].status in (
                    TaskStatus.PENDING, TaskStatus.DOWNLOADING, TaskStatus.PROCESSING
                )
            ]
            if len(user_active) >= config.MAX_USER_QUEUE:
                logger.warning("User %d queue full (%d/%d)", task.user_id, len(user_active), config.MAX_USER_QUEUE)
                return ""

            self._tasks[task.task_id] = task
            self._user_tasks.setdefault(task.user_id, []).append(task.task_id)

        # Start processing
        task._task = asyncio.create_task(self._process(task))
        return task.task_id

    async def _process(self, task: DownloadTask):
        """Process a single task with semaphore-controlled concurrency."""
        try:
            # Wait for user slot (1 concurrent per user)
            user_sem = self._get_user_semaphore(task.user_id)
            async with user_sem:
                if task.is_cancelled:
                    task.status = TaskStatus.CANCELLED
                    return

                # Wait for global slot
                async with self._global_semaphore:
                    if task.is_cancelled:
                        task.status = TaskStatus.CANCELLED
                        return

                    task.status = TaskStatus.DOWNLOADING
                    await self._execute_task(task)

        except asyncio.CancelledError:
            task.status = TaskStatus.CANCELLED
            logger.info("Task cancelled: %s", task.task_id)
        except Exception as e:
            task.status = TaskStatus.ERROR
            task.error = str(e)
            logger.error("Task error: %s — %s", task.task_id, e)
        finally:
            self._cleanup_task(task)

    async def _execute_task(self, task: DownloadTask):
        """Execute the actual download. Override in subclass or use callback."""
        # This will be called by the download_service which sets up the callback
        if hasattr(task, "_callback") and task._callback:
            await task._callback(task)
        else:
            task.status = TaskStatus.ERROR
            task.error = "No download callback configured"

    def _cleanup_task(self, task: DownloadTask):
        """Clean up task resources after completion."""
        # Keep task in dict for status queries, but remove from active list later
        pass

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a task."""
        task = self._tasks.get(task_id)
        if not task:
            return False
        task.cancel()
        if task._task and not task._task.done():
            task._task.cancel()
        task.status = TaskStatus.CANCELLED
        logger.info("Task cancelled by user: %s", task_id)
        return True

    def get_task(self, task_id: str) -> DownloadTask | None:
        """Get a task by ID."""
        return self._tasks.get(task_id)

    def get_user_tasks(self, user_id: int) -> list[DownloadTask]:
        """Get all tasks for a user."""
        task_ids = self._user_tasks.get(user_id, [])
        return [self._tasks[tid] for tid in task_ids if tid in self._tasks]

    def get_active_tasks(self) -> list[DownloadTask]:
        """Get all currently active tasks."""
        return [
            t for t in self._tasks.values()
            if t.status in (TaskStatus.DOWNLOADING, TaskStatus.PROCESSING, TaskStatus.SENDING)
        ]

    def get_all_tasks_count(self) -> dict[str, int]:
        """Get task counts by status."""
        counts: dict[str, int] = {}
        for task in self._tasks.values():
            counts[task.status.value] = counts.get(task.status.value, 0) + 1
        return counts


# Global queue instance
download_queue = DownloadQueue()
