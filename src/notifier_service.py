"""Notifier Service - FastAPI webhook receiver for GitHub events.

The Notifier service receives GitHub webhooks and creates/updates work items
in the GitHub Issues queue. It acts as the entry point for external events
that need to be processed by the Sentinel.
"""

import logging
import sys
from collections.abc import AsyncIterator, Callable, Coroutine
from contextlib import asynccontextmanager
from typing import Any

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from github_client.github_queue import GitHubQueue, GitHubQueueError
from models.work_item import TaskType, WorkItemCreate

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Global queue client
_queue: GitHubQueue | None = None


class WebhookPayload(BaseModel):
    """Generic webhook payload model."""

    action: str | None = None
    sender: dict[str, Any] | None = None
    repository: dict[str, Any] | None = None
    issue: dict[str, Any] | None = None
    pull_request: dict[str, Any] | None = None
    comment: dict[str, Any] | None = None
    review: dict[str, Any] | None = None


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = "healthy"
    service: str = "notifier"
    version: str = "0.1.0"


class QueueStatusResponse(BaseModel):
    """Queue status response model."""

    connected: bool
    repository: str | None = None


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Manage application lifecycle."""
    global _queue

    # Startup: Initialize queue client
    import os

    token = os.getenv("NOTIFIER_GITHUB_TOKEN", "")
    org = os.getenv("NOTIFIER_GITHUB_ORG", "")
    repo = os.getenv("NOTIFIER_GITHUB_REPO", "")

    if token and org and repo:
        _queue = GitHubQueue(token=token, org=org, repo=repo)
        logger.info(f"Queue initialized for {org}/{repo}")
    else:
        logger.warning("Queue not configured - NOTIFIER_GITHUB_TOKEN, ORG, or REPO missing")

    yield

    # Shutdown: Clean up
    if _queue:
        await _queue.close()
        _queue = None
        logger.info("Queue client closed")


app = FastAPI(
    title="Notifier Service",
    description="Webhook receiver for GitHub events in the workflow orchestration queue",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse()


@app.get("/queue/status", response_model=QueueStatusResponse)
async def queue_status() -> QueueStatusResponse:
    """Check queue connection status."""
    if _queue:
        return QueueStatusResponse(connected=True, repository=_queue.repo_path)
    return QueueStatusResponse(connected=False)


@app.post("/webhook/github")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
) -> JSONResponse:
    """Handle GitHub webhook events.

    This endpoint receives GitHub webhook payloads and processes them
    asynchronously. It validates the event type and dispatches to
    appropriate handlers.
    """
    # Get event type from headers
    event_type = request.headers.get("X-GitHub-Event", "")
    if not event_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing X-GitHub-Event header",
        )

    # Parse payload
    try:
        payload_data = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse webhook payload: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        ) from None

    payload = WebhookPayload(**payload_data)

    # Log the event
    logger.info(f"Received {event_type} event with action: {payload.action}")

    # Process in background
    background_tasks.add_task(
        process_webhook_event,
        event_type,
        payload,
    )

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={"status": "accepted", "event": event_type},
    )


async def process_webhook_event(event_type: str, payload: WebhookPayload) -> None:
    """Process a webhook event asynchronously.

    Args:
        event_type: The GitHub event type (e.g., 'issues', 'push').
        payload: The webhook payload.
    """
    if not _queue:
        logger.warning("Queue not configured, skipping event processing")
        return

    try:
        handler = get_event_handler(event_type)
        if handler:
            work_item = await handler(payload)
            if work_item:
                await _queue.create_issue(work_item)
                logger.info(f"Created work item from {event_type} event")
        else:
            logger.debug(f"No handler for event type: {event_type}")

    except GitHubQueueError as e:
        logger.error(f"Failed to process {event_type} event: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error processing {event_type} event: {e}")


def get_event_handler(
    event_type: str,
) -> Callable[[WebhookPayload], Coroutine[Any, Any, WorkItemCreate | None]] | None:
    """Get the appropriate handler for an event type.

    Args:
        event_type: The GitHub event type.

    Returns:
        Handler function or None if not supported.
    """
    handlers = {
        "issues": handle_issues_event,
        "pull_request": handle_pull_request_event,
        "pull_request_review": handle_review_event,
        "issue_comment": handle_comment_event,
        "push": handle_push_event,
        "workflow_dispatch": handle_workflow_dispatch_event,
    }
    return handlers.get(event_type)


async def handle_issues_event(payload: WebhookPayload) -> WorkItemCreate | None:
    """Handle GitHub Issues events.

    Args:
        payload: The webhook payload.

    Returns:
        WorkItemCreate if a new work item should be created.
    """
    if not payload.issue:
        return None

    action = payload.action or ""
    issue = payload.issue

    # Only create work items for new issues with specific labels
    if action == "opened":
        labels = [label["name"] for label in issue.get("labels", [])]
        if "queued" in labels or "process" in labels:
            return WorkItemCreate(
                title=f"[Issue #{issue['number']}] {issue.get('title', 'Untitled')}",
                body=issue.get("body"),
                task_type=TaskType.ISSUE,
                labels=labels,
                metadata={"source_issue": issue["number"]},
            )

    return None


async def handle_pull_request_event(payload: WebhookPayload) -> WorkItemCreate | None:
    """Handle Pull Request events.

    Args:
        payload: The webhook payload.

    Returns:
        WorkItemCreate if a new work item should be created.
    """
    if not payload.pull_request:
        return None

    action = payload.action or ""
    pr = payload.pull_request

    # Create work item for PR reviews
    if action in ("review_requested", "ready_for_review"):
        return WorkItemCreate(
            title=f"[PR #{pr['number']}] Review required: {pr.get('title', 'Untitled')}",
            body=pr.get("body"),
            task_type=TaskType.PR_REVIEW,
            labels=["pr-review", "queued"],
            metadata={"source_pr": pr["number"]},
        )

    return None


async def handle_review_event(payload: WebhookPayload) -> WorkItemCreate | None:
    """Handle Pull Request Review events.

    Args:
        payload: The webhook payload.

    Returns:
        WorkItemCreate if a new work item should be created.
    """
    if not payload.review or not payload.pull_request:
        return None

    action = payload.action or ""
    review = payload.review
    pr = payload.pull_request

    # Create work item for review responses
    if action == "submitted" and review.get("state") == "changes_requested":
        return WorkItemCreate(
            title=f"[PR #{pr['number']}] Address review feedback",
            body=f"Review URL: {review.get('html_url')}",
            task_type=TaskType.PR_REVIEW,
            labels=["pr-feedback", "queued"],
            metadata={"source_pr": pr["number"], "review_id": review.get("id")},
        )

    return None


async def handle_comment_event(payload: WebhookPayload) -> WorkItemCreate | None:
    """Handle Issue Comment events.

    Args:
        payload: The webhook payload.

    Returns:
        WorkItemCreate if a new work item should be created.
    """
    if not payload.comment or not payload.issue:
        return None

    action = payload.action or ""
    comment = payload.comment
    issue = payload.issue

    # Create work item for commands in comments
    if action == "created":
        body = comment.get("body", "")
        # Check for command patterns like /process or /queue
        if body.strip().startswith(("/process", "/queue")):
            return WorkItemCreate(
                title=f"[Issue #{issue['number']}] Process command",
                body=body,
                task_type=TaskType.PR_COMMENT,
                labels=["command", "queued"],
                metadata={"source_issue": issue["number"], "comment_id": comment.get("id")},
            )

    return None


async def handle_push_event(payload: WebhookPayload) -> WorkItemCreate | None:
    """Handle Push events.

    Args:
        payload: The webhook payload.

    Returns:
        WorkItemCreate if a new work item should be created.
    """
    # Push events typically don't create work items automatically
    # This can be customized based on specific needs
    logger.debug(f"Push event received for {payload.repository}")
    return None


async def handle_workflow_dispatch_event(payload: WebhookPayload) -> WorkItemCreate | None:
    """Handle Workflow Dispatch events.

    Args:
        payload: The webhook payload.

    Returns:
        WorkItemCreate if a new work item should be created.
    """
    # Workflow dispatch can be used to trigger specific tasks
    action = payload.action or ""

    if action == "workflow_dispatch":
        return WorkItemCreate(
            title="[Workflow] Dispatch triggered",
            body=f"Workflow dispatch received with action: {action}",
            task_type=TaskType.WORKFLOW_DISPATCH,
            labels=["workflow", "queued"],
        )

    return None


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "notifier_service:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
