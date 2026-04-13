"""GitHub Issues API wrapper for using GitHub Issues as a task queue."""

import logging
from typing import Any

import httpx
from pydantic import ValidationError

from models.work_item import TaskType, WorkItem, WorkItemCreate, WorkItemStatus, WorkItemUpdate

logger = logging.getLogger(__name__)


class GitHubQueueError(Exception):
    """Base exception for GitHub queue operations."""

    pass


class GitHubAuthError(GitHubQueueError):
    """Authentication error with GitHub API."""

    pass


class GitHubRateLimitError(GitHubQueueError):
    """Rate limit exceeded for GitHub API."""

    pass


class GitHubQueue:
    """Wrapper for GitHub Issues API to use Issues as a task queue.

    This class provides methods to interact with GitHub Issues for
    workflow orchestration, treating issues as work items in a queue.
    """

    GITHUB_API_BASE = "https://api.github.com"

    def __init__(
        self,
        token: str,
        org: str,
        repo: str,
        *,
        base_url: str | None = None,
    ) -> None:
        """Initialize GitHub queue client.

        Args:
            token: GitHub personal access token with repo permissions.
            org: GitHub organization or user name.
            repo: Repository name.
            base_url: Optional base URL for GitHub API (for GitHub Enterprise).
        """
        self.token = token
        self.org = org
        self.repo = repo
        self.base_url = (base_url or self.GITHUB_API_BASE).rstrip("/")
        self._client: httpx.AsyncClient | None = None

    @property
    def repo_path(self) -> str:
        """Return the full repository path (org/repo)."""
        return f"{self.org}/{self.repo}"

    def _get_headers(self) -> dict[str, str]:
        """Get HTTP headers for GitHub API requests."""
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers=self._get_headers(),
                timeout=30.0,
                follow_redirects=True,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make an authenticated request to GitHub API.

        Args:
            method: HTTP method.
            endpoint: API endpoint (without base URL).
            **kwargs: Additional arguments for httpx.

        Returns:
            Parsed JSON response.

        Raises:
            GitHubAuthError: If authentication fails.
            GitHubRateLimitError: If rate limit is exceeded.
            GitHubQueueError: For other API errors.
        """
        client = await self._get_client()
        url = f"{self.base_url}{endpoint}"

        response = await client.request(method, url, **kwargs)

        if response.status_code == 401:
            raise GitHubAuthError("GitHub authentication failed")
        if response.status_code == 403:
            if "rate limit" in response.text.lower():
                raise GitHubRateLimitError("GitHub API rate limit exceeded")
            raise GitHubQueueError(f"Access forbidden: {response.text}")
        if response.status_code >= 400:
            raise GitHubQueueError(f"GitHub API error: {response.status_code} - {response.text}")

        return response.json()

    async def list_issues(
        self,
        *,
        state: str = "open",
        labels: list[str] | None = None,
        sort: str = "created",
        direction: str = "desc",
        per_page: int = 100,
        page: int = 1,
    ) -> list[WorkItem]:
        """List issues in the repository.

        Args:
            state: Issue state (open, closed, all).
            labels: Filter by labels.
            sort: Sort field (created, updated, comments).
            direction: Sort direction (asc, desc).
            per_page: Results per page (max 100).
            page: Page number.

        Returns:
            List of WorkItems.
        """
        params: dict[str, Any] = {
            "state": state,
            "sort": sort,
            "direction": direction,
            "per_page": min(per_page, 100),
            "page": page,
        }
        if labels:
            params["labels"] = ",".join(labels)

        data = await self._request("GET", f"/repos/{self.repo_path}/issues", params=params)
        items = []

        for issue in data:
            try:
                # Extract task type from labels
                task_type = TaskType.ISSUE
                for label in issue.get("labels", []):
                    label_name = label.get("name", "")
                    try:
                        task_type = TaskType(label_name.lower())
                        break
                    except ValueError:
                        continue

                item = WorkItem(
                    issue_number=issue["number"],
                    title=issue["title"],
                    body=issue.get("body"),
                    task_type=task_type,
                    status=WorkItemStatus.PENDING,
                    labels=[label["name"] for label in issue.get("labels", [])],
                    assignees=[a["login"] for a in issue.get("assignees", [])],
                    created_at=issue.get("created_at"),
                    updated_at=issue.get("updated_at"),
                )
                items.append(item)
            except (KeyError, ValidationError) as e:
                logger.warning(f"Failed to parse issue: {e}")
                continue

        return items

    async def get_issue(self, issue_number: int) -> WorkItem | None:
        """Get a specific issue by number.

        Args:
            issue_number: The issue number.

        Returns:
            WorkItem or None if not found.
        """
        try:
            data = await self._request("GET", f"/repos/{self.repo_path}/issues/{issue_number}")

            # Extract task type from labels
            task_type = TaskType.ISSUE
            for label in data.get("labels", []):
                label_name = label.get("name", "")
                try:
                    task_type = TaskType(label_name.lower())
                    break
                except ValueError:
                    continue

            return WorkItem(
                issue_number=data["number"],
                title=data["title"],
                body=data.get("body"),
                task_type=task_type,
                status=WorkItemStatus.PENDING,
                labels=[label["name"] for label in data.get("labels", [])],
                assignees=[a["login"] for a in data.get("assignees", [])],
                created_at=data.get("created_at"),
                updated_at=data.get("updated_at"),
            )
        except GitHubQueueError as e:
            logger.error(f"Failed to get issue {issue_number}: {e}")
            return None

    async def create_issue(self, work_item: WorkItemCreate) -> WorkItem:
        """Create a new issue.

        Args:
            work_item: WorkItemCreate model with issue data.

        Returns:
            Created WorkItem.
        """
        payload = {
            "title": work_item.title,
            "body": work_item.body,
            "labels": work_item.labels,
            "assignees": work_item.assignees,
        }

        data = await self._request("POST", f"/repos/{self.repo_path}/issues", json=payload)

        return WorkItem(
            issue_number=data["number"],
            title=data["title"],
            body=data.get("body"),
            task_type=work_item.task_type,
            status=WorkItemStatus.PENDING,
            labels=[label["name"] for label in data.get("labels", [])],
            assignees=[assignee["login"] for assignee in data.get("assignees", [])],
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            metadata=work_item.metadata,
        )

    async def update_issue(self, issue_number: int, update: WorkItemUpdate) -> WorkItem | None:
        """Update an existing issue.

        Args:
            issue_number: The issue number.
            update: WorkItemUpdate model with fields to update.

        Returns:
            Updated WorkItem or None if failed.
        """
        payload: dict[str, Any] = {}

        if update.title is not None:
            payload["title"] = update.title
        if update.body is not None:
            payload["body"] = update.body
        if update.labels is not None:
            payload["labels"] = update.labels
        if update.assignees is not None:
            payload["assignees"] = update.assignees

        try:
            data = await self._request(
                "PATCH",
                f"/repos/{self.repo_path}/issues/{issue_number}",
                json=payload,
            )

            # Extract task type from labels
            task_type = TaskType.ISSUE
            for label in data.get("labels", []):
                label_name = label.get("name", "")
                try:
                    task_type = TaskType(label_name.lower())
                    break
                except ValueError:
                    continue

            return WorkItem(
                issue_number=data["number"],
                title=data["title"],
                body=data.get("body"),
                task_type=task_type,
                status=update.status or WorkItemStatus.PENDING,
                labels=[label["name"] for label in data.get("labels", [])],
                assignees=[a["login"] for a in data.get("assignees", [])],
                created_at=data.get("created_at"),
                updated_at=data.get("updated_at"),
                metadata=update.metadata or {},
            )
        except GitHubQueueError as e:
            logger.error(f"Failed to update issue {issue_number}: {e}")
            return None

    async def close_issue(self, issue_number: int) -> bool:
        """Close an issue.

        Args:
            issue_number: The issue number.

        Returns:
            True if successful, False otherwise.
        """
        try:
            await self._request(
                "PATCH",
                f"/repos/{self.repo_path}/issues/{issue_number}",
                json={"state": "closed"},
            )
            return True
        except GitHubQueueError as e:
            logger.error(f"Failed to close issue {issue_number}: {e}")
            return False

    async def add_labels(self, issue_number: int, labels: list[str]) -> list[str]:
        """Add labels to an issue.

        Args:
            issue_number: The issue number.
            labels: Labels to add.

        Returns:
            List of all labels on the issue.
        """
        data = await self._request(
            "POST",
            f"/repos/{self.repo_path}/issues/{issue_number}/labels",
            json={"labels": labels},
        )
        return [label["name"] for label in data]

    async def remove_label(self, issue_number: int, label: str) -> list[str]:
        """Remove a label from an issue.

        Args:
            issue_number: The issue number.
            label: Label to remove.

        Returns:
            List of remaining labels.
        """
        data = await self._request(
            "DELETE",
            f"/repos/{self.repo_path}/issues/{issue_number}/labels/{label}",
        )
        return [label["name"] for label in data]

    async def add_comment(self, issue_number: int, body: str) -> dict[str, Any]:
        """Add a comment to an issue.

        Args:
            issue_number: The issue number.
            body: Comment body.

        Returns:
            Created comment data.
        """
        return await self._request(
            "POST",
            f"/repos/{self.repo_path}/issues/{issue_number}/comments",
            json={"body": body},
        )
