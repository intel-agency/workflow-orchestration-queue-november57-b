"""Tests for the Notifier webhook service."""

import pytest
from fastapi.testclient import TestClient

# Mark all tests in this module as async
pytestmark = pytest.mark.asyncio


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    async def test_health_check(self) -> None:
        """Test health check returns healthy status."""
        from notifier_service import app

        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "notifier"


class TestQueueStatusEndpoint:
    """Tests for queue status endpoint."""

    async def test_queue_status_without_config(self) -> None:
        """Test queue status when not configured."""
        from notifier_service import app

        client = TestClient(app)
        response = client.get("/queue/status")

        assert response.status_code == 200
        data = response.json()
        assert data["connected"] is False


class TestWebhookEndpoint:
    """Tests for GitHub webhook endpoint."""

    async def test_webhook_missing_event_header(self) -> None:
        """Test webhook rejects requests without X-GitHub-Event header."""
        from notifier_service import app

        client = TestClient(app)
        response = client.post("/webhook/github", json={})

        assert response.status_code == 400

    async def test_webhook_invalid_json(self) -> None:
        """Test webhook rejects invalid JSON."""
        from notifier_service import app

        client = TestClient(app)
        response = client.post(
            "/webhook/github",
            content=b"not json",
            headers={"X-GitHub-Event": "push"},
        )

        assert response.status_code == 400

    async def test_webhook_valid_event(self) -> None:
        """Test webhook accepts valid events."""
        from notifier_service import app

        client = TestClient(app)
        response = client.post(
            "/webhook/github",
            json={"action": "opened"},
            headers={"X-GitHub-Event": "issues"},
        )

        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "accepted"
        assert data["event"] == "issues"


class TestEventHandlers:
    """Tests for webhook event handlers."""

    async def test_handle_issues_event(self) -> None:
        """Test issues event handler."""
        from models.work_item import TaskType
        from notifier_service import handle_issues_event

        payload = type(
            "WebhookPayload",
            (),
            {
                "action": "opened",
                "issue": {
                    "number": 42,
                    "title": "Test Issue",
                    "body": "Test body",
                    "labels": [{"name": "queued"}],
                },
            },
        )()

        result = await handle_issues_event(payload)

        assert result is not None
        assert result.task_type == TaskType.ISSUE
        assert "queued" in result.labels

    async def test_handle_issues_event_without_label(self) -> None:
        """Test issues event handler without process label."""
        from notifier_service import handle_issues_event

        payload = type(
            "WebhookPayload",
            (),
            {
                "action": "opened",
                "issue": {
                    "number": 42,
                    "title": "Test Issue",
                    "body": "Test body",
                    "labels": [{"name": "bug"}],
                },
            },
        )()

        result = await handle_issues_event(payload)

        assert result is None

    async def test_handle_pull_request_event(self) -> None:
        """Test pull request event handler."""
        from models.work_item import TaskType
        from notifier_service import handle_pull_request_event

        payload = type(
            "WebhookPayload",
            (),
            {
                "action": "review_requested",
                "pull_request": {
                    "number": 10,
                    "title": "Test PR",
                    "body": "Test PR body",
                },
            },
        )()

        result = await handle_pull_request_event(payload)

        assert result is not None
        assert result.task_type == TaskType.PR_REVIEW
        assert "pr-review" in result.labels

    async def test_handle_comment_event_with_command(self) -> None:
        """Test comment event handler with command."""
        from notifier_service import handle_comment_event

        payload = type(
            "WebhookPayload",
            (),
            {
                "action": "created",
                "comment": {"body": "/process this issue", "id": 123},
                "issue": {"number": 5},
            },
        )()

        result = await handle_comment_event(payload)

        assert result is not None
        assert "command" in result.labels
