"""Sentinel - Background service for processing work items from GitHub Issues queue.

The Sentinel service monitors GitHub Issues for tasks, processes them, and
updates their status. It runs as a background daemon that periodically polls
for new work items.
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime
from typing import Any

from pydantic_settings import BaseSettings

from github_client.github_queue import GitHubQueue, GitHubQueueError
from models.work_item import WorkItem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


class SentinelSettings(BaseSettings):
    """Configuration settings for the Sentinel service."""

    # GitHub configuration
    github_token: str = ""
    github_org: str = ""
    github_repo: str = ""

    # Sentinel configuration
    poll_interval_seconds: int = 60
    max_concurrent_tasks: int = 5
    queue_labels: list[str] = ["queued"]
    processing_label: str = "in-progress"
    completed_label: str = "completed"
    failed_label: str = "failed"

    # Health check
    health_check_port: int = 8080

    model_config = {
        "env_prefix": "SENTINEL_",
        "env_file": ".env",
        "extra": "ignore",
    }


class Sentinel:
    """Background service that processes work items from GitHub Issues.

    The Sentinel polls GitHub Issues for items with specific labels,
    processes them, and updates their status via labels and comments.
    """

    def __init__(self, settings: SentinelSettings | None = None) -> None:
        """Initialize the Sentinel service.

        Args:
            settings: Optional settings override. If not provided, loads from environment.
        """
        self.settings = settings or SentinelSettings()
        self._running = False
        self._queue: GitHubQueue | None = None
        self._shutdown_event = asyncio.Event()

        logger.info(
            f"Sentinel initialized for {self.settings.github_org}/{self.settings.github_repo}"
        )

    def _create_queue(self) -> GitHubQueue:
        """Create GitHub queue client."""
        return GitHubQueue(
            token=self.settings.github_token,
            org=self.settings.github_org,
            repo=self.settings.github_repo,
        )

    async def start(self) -> None:
        """Start the Sentinel service."""
        if self._running:
            logger.warning("Sentinel is already running")
            return

        self._running = True
        self._queue = self._create_queue()

        # Set up signal handlers for graceful shutdown
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(self.stop()))

        logger.info("Sentinel service started")

        try:
            await self._run_loop()
        except Exception as e:
            logger.exception(f"Sentinel crashed: {e}")
            raise
        finally:
            await self.stop()

    async def stop(self) -> None:
        """Stop the Sentinel service gracefully."""
        if not self._running:
            return

        logger.info("Stopping Sentinel service...")
        self._running = False
        self._shutdown_event.set()

        if self._queue:
            await self._queue.close()
            self._queue = None

        logger.info("Sentinel service stopped")

    async def _run_loop(self) -> None:
        """Main processing loop."""
        while self._running:
            try:
                await self._process_queue()
            except Exception as e:
                logger.exception(f"Error processing queue: {e}")

            # Wait for next poll interval or shutdown
            try:
                await asyncio.wait_for(
                    self._shutdown_event.wait(),
                    timeout=self.settings.poll_interval_seconds,
                )
                # If we get here, shutdown was signaled
                break
            except TimeoutError:
                # Normal timeout, continue polling
                pass

    async def _process_queue(self) -> None:
        """Process items in the queue."""
        if not self._queue:
            logger.error("Queue not initialized")
            return

        logger.info("Polling for work items...")

        try:
            # Get items with queue labels
            items = await self._queue.list_issues(
                state="open",
                labels=self.settings.queue_labels,
            )

            logger.info(f"Found {len(items)} items in queue")

            # Process items with concurrency limit
            semaphore = asyncio.Semaphore(self.settings.max_concurrent_tasks)

            async def process_with_limit(item: WorkItem) -> None:
                async with semaphore:
                    await self._process_item(item)

            tasks = [process_with_limit(item) for item in items]
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

        except GitHubQueueError as e:
            logger.error(f"Failed to poll queue: {e}")

    async def _process_item(self, item: WorkItem) -> None:
        """Process a single work item.

        Args:
            item: The work item to process.
        """
        if not self._queue:
            return

        logger.info(f"Processing item #{item.issue_number}: {item.title}")

        try:
            # Mark as in progress
            await self._queue.add_labels(item.issue_number, [self.settings.processing_label])

            # Process the item (placeholder for actual processing logic)
            result = await self._execute_task(item)

            if result.success:
                # Mark as completed
                await self._queue.add_labels(item.issue_number, [self.settings.completed_label])
                await self._queue.remove_label(item.issue_number, self.settings.processing_label)
                await self._queue.add_comment(
                    item.issue_number,
                    f"✅ Task completed at {datetime.utcnow().isoformat()}Z",
                )
                logger.info(f"Item #{item.issue_number} completed successfully")
            else:
                # Mark as failed
                await self._queue.add_labels(item.issue_number, [self.settings.failed_label])
                await self._queue.remove_label(item.issue_number, self.settings.processing_label)
                await self._queue.add_comment(
                    item.issue_number,
                    f"❌ Task failed at {datetime.utcnow().isoformat()}Z: {result.error}",
                )
                logger.error(f"Item #{item.issue_number} failed: {result.error}")

        except GitHubQueueError as e:
            logger.error(f"Failed to process item #{item.issue_number}: {e}")

    async def _execute_task(self, item: WorkItem) -> "TaskResult":
        """Execute the actual task logic.

        This is a placeholder method that should be overridden or extended
        with actual task processing logic.

        Args:
            item: The work item to execute.

        Returns:
            TaskResult indicating success or failure.
        """
        # Placeholder implementation
        await asyncio.sleep(1)  # Simulate work
        return TaskResult(success=True, output=f"Processed {item.task_type} task")


class TaskResult:
    """Result of a task execution."""

    def __init__(
        self,
        *,
        success: bool,
        output: str = "",
        error: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Initialize task result.

        Args:
            success: Whether the task succeeded.
            output: Output message on success.
            error: Error message on failure.
            metadata: Additional metadata.
        """
        self.success = success
        self.output = output
        self.error = error
        self.metadata = metadata or {}


async def main() -> None:
    """Main entry point for the Sentinel service."""
    settings = SentinelSettings()

    # Validate required settings
    if not settings.github_token:
        logger.error("SENTINEL_GITHUB_TOKEN is required")
        sys.exit(1)
    if not settings.github_org:
        logger.error("SENTINEL_GITHUB_ORG is required")
        sys.exit(1)
    if not settings.github_repo:
        logger.error("SENTINEL_GITHUB_REPO is required")
        sys.exit(1)

    sentinel = Sentinel(settings)
    await sentinel.start()


if __name__ == "__main__":
    asyncio.run(main())
