"""WorkItem models for workflow orchestration queue."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class TaskType(StrEnum):
    """Types of tasks that can be processed."""

    ISSUE = "issue"
    PR_REVIEW = "pr_review"
    PR_COMMENT = "pr_comment"
    WORKFLOW_DISPATCH = "workflow_dispatch"
    WEBHOOK = "webhook"


class WorkItemStatus(StrEnum):
    """Status of a work item in the queue."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkItem(BaseModel):
    """Represents a work item in the orchestration queue.

    A WorkItem is a GitHub Issue that represents a task to be processed
    by the Sentinel service.
    """

    issue_number: int = Field(..., description="GitHub issue number", ge=1)
    title: str = Field(..., description="Issue title", min_length=1)
    body: str | None = Field(default=None, description="Issue body/description")
    task_type: TaskType = Field(..., description="Type of task")
    status: WorkItemStatus = Field(
        default=WorkItemStatus.PENDING,
        description="Current status of the work item",
    )
    labels: list[str] = Field(default_factory=list, description="GitHub labels")
    assignees: list[str] = Field(default_factory=list, description="GitHub assignees")
    created_at: str | None = Field(default=None, description="ISO 8601 creation timestamp")
    updated_at: str | None = Field(default=None, description="ISO 8601 update timestamp")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata for processing",
    )

    model_config = {
        "use_enum_values": True,
        "json_schema_extra": {
            "examples": [
                {
                    "issue_number": 42,
                    "title": "Implement new feature",
                    "body": "Description of the feature...",
                    "task_type": "issue",
                    "status": "pending",
                    "labels": ["enhancement", "priority:high"],
                    "assignees": ["developer1"],
                    "created_at": "2024-01-15T10:30:00Z",
                    "updated_at": "2024-01-15T10:30:00Z",
                    "metadata": {"source": "webhook", "priority": 1},
                }
            ]
        },
    }


class WorkItemCreate(BaseModel):
    """Model for creating a new work item."""

    title: str = Field(..., min_length=1, max_length=500)
    body: str | None = None
    task_type: TaskType = Field(default=TaskType.ISSUE)
    labels: list[str] = Field(default_factory=list)
    assignees: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkItemUpdate(BaseModel):
    """Model for updating a work item."""

    title: str | None = Field(default=None, min_length=1, max_length=500)
    body: str | None = None
    status: WorkItemStatus | None = None
    labels: list[str] | None = None
    assignees: list[str] | None = None
    metadata: dict[str, Any] | None = None
