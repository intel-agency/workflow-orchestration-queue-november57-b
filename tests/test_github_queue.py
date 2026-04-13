"""Tests for GitHub Issues API wrapper."""

from unittest.mock import MagicMock, patch

import pytest

# Mark all tests in this module as async
pytestmark = pytest.mark.asyncio


class TestGitHubQueue:
    """Tests for GitHubQueue class."""

    async def test_queue_initialization(self) -> None:
        """Test GitHubQueue can be initialized."""
        from github_client.github_queue import GitHubQueue

        queue = GitHubQueue(
            token="test-token",
            org="test-org",
            repo="test-repo",
        )

        assert queue.token == "test-token"
        assert queue.org == "test-org"
        assert queue.repo == "test-repo"
        assert queue.repo_path == "test-org/test-repo"

    async def test_queue_with_custom_base_url(self) -> None:
        """Test GitHubQueue with custom base URL for GitHub Enterprise."""
        from github_client.github_queue import GitHubQueue

        queue = GitHubQueue(
            token="test-token",
            org="test-org",
            repo="test-repo",
            base_url="https://github.example.com/api/v3",
        )

        assert queue.base_url == "https://github.example.com/api/v3"

    async def test_get_headers(self) -> None:
        """Test HTTP headers are correctly set."""
        from github_client.github_queue import GitHubQueue

        queue = GitHubQueue(
            token="test-token",
            org="test-org",
            repo="test-repo",
        )

        headers = queue._get_headers()

        assert headers["Authorization"] == "Bearer test-token"
        assert headers["Accept"] == "application/vnd.github+json"
        assert "X-GitHub-Api-Version" in headers

    async def test_close_client(self) -> None:
        """Test closing the HTTP client."""
        from github_client.github_queue import GitHubQueue

        queue = GitHubQueue(
            token="test-token",
            org="test-org",
            repo="test-repo",
        )

        # Close should not raise even if client was never used
        await queue.close()
        assert queue._client is None


class TestGitHubQueueErrors:
    """Tests for GitHubQueue error handling."""

    async def test_auth_error(self) -> None:
        """Test GitHubAuthError is raised on 401."""
        from github_client.github_queue import GitHubAuthError, GitHubQueue

        queue = GitHubQueue(
            token="invalid-token",
            org="test-org",
            repo="test-repo",
        )

        # Test that _request raises GitHubAuthError on 401
        with patch("github_client.github_queue.httpx.AsyncClient.request") as mock_request:
            import httpx

            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.text = "Unauthorized"
            mock_request.return_value = mock_response

            with pytest.raises(GitHubAuthError):
                await queue._request("GET", "/test")

    async def test_rate_limit_error(self) -> None:
        """Test GitHubRateLimitError is raised on rate limit."""
        from github_client.github_queue import GitHubQueue, GitHubRateLimitError

        queue = GitHubQueue(
            token="test-token",
            org="test-org",
            repo="test-repo",
        )

        with patch("github_client.github_queue.httpx.AsyncClient.request") as mock_request:
            import httpx

            mock_response = MagicMock()
            mock_response.status_code = 403
            mock_response.text = "rate limit exceeded"
            mock_request.return_value = mock_response

            with pytest.raises(GitHubRateLimitError):
                await queue._request("GET", "/test")


class TestWorkItemModels:
    """Tests for WorkItem model usage with queue."""

    async def test_create_work_item(self) -> None:
        """Test creating a WorkItem from model."""
        from models.work_item import TaskType, WorkItem, WorkItemStatus

        item = WorkItem(
            issue_number=1,
            title="Test Task",
            body="Test body",
            task_type=TaskType.ISSUE,
            status=WorkItemStatus.PENDING,
            labels=["queued"],
        )

        assert item.issue_number == 1
        assert item.title == "Test Task"
        assert item.task_type == TaskType.ISSUE
        assert item.status == WorkItemStatus.PENDING

    async def test_work_item_create_model(self) -> None:
        """Test WorkItemCreate model."""
        from models.work_item import TaskType, WorkItemCreate

        create = WorkItemCreate(
            title="New Task",
            body="Task description",
            task_type=TaskType.PR_REVIEW,
            labels=["pr-review"],
        )

        assert create.title == "New Task"
        assert create.task_type == TaskType.PR_REVIEW

    async def test_work_item_update_model(self) -> None:
        """Test WorkItemUpdate model."""
        from models.work_item import WorkItemStatus, WorkItemUpdate

        update = WorkItemUpdate(
            title="Updated Title",
            status=WorkItemStatus.COMPLETED,
        )

        assert update.title == "Updated Title"
        assert update.status == WorkItemStatus.COMPLETED
        assert update.body is None


class TestTaskTypeEnum:
    """Tests for TaskType enum."""

    def test_task_types(self) -> None:
        """Test TaskType enum values."""
        from models.work_item import TaskType

        assert TaskType.ISSUE == "issue"
        assert TaskType.PR_REVIEW == "pr_review"
        assert TaskType.PR_COMMENT == "pr_comment"
        assert TaskType.WORKFLOW_DISPATCH == "workflow_dispatch"
        assert TaskType.WEBHOOK == "webhook"


class TestWorkItemStatusEnum:
    """Tests for WorkItemStatus enum."""

    def test_status_values(self) -> None:
        """Test WorkItemStatus enum values."""
        from models.work_item import WorkItemStatus

        assert WorkItemStatus.PENDING == "pending"
        assert WorkItemStatus.IN_PROGRESS == "in_progress"
        assert WorkItemStatus.COMPLETED == "completed"
        assert WorkItemStatus.FAILED == "failed"
        assert WorkItemStatus.CANCELLED == "cancelled"
