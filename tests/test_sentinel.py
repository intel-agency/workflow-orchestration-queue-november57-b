"""Tests for the Sentinel background service."""

import pytest

# Mark all tests in this module as async
pytestmark = pytest.mark.asyncio


class TestSentinelSettings:
    """Tests for SentinelSettings configuration."""

    async def test_default_settings(self) -> None:
        """Test default settings values."""
        from orchestrator_sentinel import SentinelSettings

        settings = SentinelSettings(
            github_token="test-token",
            github_org="test-org",
            github_repo="test-repo",
        )

        assert settings.poll_interval_seconds == 60
        assert settings.max_concurrent_tasks == 5
        assert settings.queue_labels == ["queued"]
        assert settings.processing_label == "in-progress"

    async def test_custom_settings(self) -> None:
        """Test custom settings values."""
        from orchestrator_sentinel import SentinelSettings

        settings = SentinelSettings(
            github_token="test-token",
            github_org="test-org",
            github_repo="test-repo",
            poll_interval_seconds=30,
            max_concurrent_tasks=10,
        )

        assert settings.poll_interval_seconds == 30
        assert settings.max_concurrent_tasks == 10


class TestSentinel:
    """Tests for Sentinel service."""

    async def test_sentinel_initialization(self) -> None:
        """Test Sentinel can be initialized."""
        from orchestrator_sentinel import Sentinel, SentinelSettings

        settings = SentinelSettings(
            github_token="test-token",
            github_org="test-org",
            github_repo="test-repo",
        )
        sentinel = Sentinel(settings)

        assert sentinel.settings.github_org == "test-org"
        assert sentinel.settings.github_repo == "test-repo"
        assert sentinel._running is False

    async def test_sentinel_not_running_initially(self) -> None:
        """Test Sentinel is not running after initialization."""
        from orchestrator_sentinel import Sentinel, SentinelSettings

        settings = SentinelSettings(
            github_token="test-token",
            github_org="test-org",
            github_repo="test-repo",
        )
        sentinel = Sentinel(settings)

        assert not sentinel._running


class TestTaskResult:
    """Tests for TaskResult class."""

    async def test_success_result(self) -> None:
        """Test creating a successful task result."""
        from orchestrator_sentinel import TaskResult

        result = TaskResult(success=True, output="Completed successfully")

        assert result.success is True
        assert result.output == "Completed successfully"
        assert result.error == ""
        assert result.metadata == {}

    async def test_failure_result(self) -> None:
        """Test creating a failed task result."""
        from orchestrator_sentinel import TaskResult

        result = TaskResult(success=False, error="Something went wrong")

        assert result.success is False
        assert result.error == "Something went wrong"
        assert result.output == ""

    async def test_result_with_metadata(self) -> None:
        """Test creating a result with metadata."""
        from orchestrator_sentinel import TaskResult

        result = TaskResult(
            success=True,
            output="Done",
            metadata={"duration": 1.5, "items_processed": 10},
        )

        assert result.metadata["duration"] == 1.5
        assert result.metadata["items_processed"] == 10
