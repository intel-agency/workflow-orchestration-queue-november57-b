# Tech Stack — workflow-orchestration-queue (OS-APOW)

> **Source:** Extracted from OS-APOW Development Plan v4.2, Architecture Guide v3.2, and Implementation Specification v1.2.

---

## Primary Language

| Component | Language | Version |
|-----------|----------|---------|
| Application Logic | Python | 3.12+ |
| Shell Bridge Scripts | Bash / PowerShell Core (pwsh) | — |

Python 3.12+ is chosen for its native async/await improvements, enhanced error messages, and performance gains over earlier versions. All application code uses type hints (mypy strict mode) and Pydantic for data validation.

---

## Core Dependencies

### Application Framework

| Package | Version Constraint | Purpose |
|---------|-------------------|---------|
| **FastAPI** | `>=0.110` | High-performance async web framework for the Notifier webhook receiver. Chosen for native Pydantic integration, automatic OpenAPI docs, and async request handling. |
| **Uvicorn** | `>=0.29` | ASGI server for running the FastAPI application in production. |
| **Pydantic** | `>=2.6` | Data validation and settings management. Used for `WorkItem`, `TaskType`, `WorkItemStatus` models and `BaseSettings` configuration. |
| **pydantic-settings** | `>=2.2` | Settings management via environment variables with `BaseSettings` (env prefix support, `.env` file loading). |
| **httpx** | `>=0.27` | Fully async HTTP client for GitHub REST API calls. Connection pooling via long-lived `AsyncClient` instances. Replaces `requests` to avoid blocking the event loop. |

### Development & Quality

| Package | Version Constraint | Purpose |
|---------|-------------------|---------|
| **pytest** | `>=8.0` | Test framework with `pytest-asyncio` plugin for async test support. |
| **pytest-asyncio** | `>=0.23` | Async test mode for pytest (`async def test_*`). |
| **pytest-cov** | `>=4.1` | Coverage reporting (`--cov=src`). Target: 80%+. |
| **ruff** | `>=0.3` | Fast Python linter and formatter (replaces flake8, black, isort). Line-length: 100. |
| **mypy** | `>=1.8` | Static type checking in strict mode. All functions require type hints. |

### Package Management

| Tool | Purpose |
|------|---------|
| **uv** | Rust-based Python package manager and resolver. Replaces pip/poetry. Manages `pyproject.toml` and `uv.lock` for deterministic builds. |
| **uv.lock** | Lockfile ensuring exact dependency versions across environments. |

---

## Infrastructure & Runtime

### Container Runtime

| Component | Technology | Details |
|-----------|-----------|---------|
| **Worker Isolation** | Docker / DevContainers | Ephemeral containers with strict resource limits (2 CPUs, 4GB RAM) |
| **Network Isolation** | Docker bridge network | Workers cannot access host subnet or peer containers |
| **DevContainer** | `.devcontainer/` config | Prebuilt GHCR image for reproducible environments |

### Agent Runtime

| Component | Technology | Details |
|-----------|-----------|---------|
| **Agent CLI** | opencode (v1.2.24) | AI agent runtime executing markdown instruction modules |
| **LLM Provider** | ZhipuAI GLM-5 | Primary model for agent inference |
| **Fallback LLM** | Kimi (Moonshot) | Secondary model access |

### CI/CD

| Component | Technology | Details |
|-----------|-----------|---------|
| **Workflows** | GitHub Actions | `validate`, `publish-docker`, `prebuild-devcontainer`, `orchestrator-agent` |
| **Validation** | `scripts/validate.ps1` | Unified lint/scan/test script for local and CI use |
| **Image Publishing** | GHCR (GitHub Container Registry) | Devcontainer images tagged with branch and version prefix |

---

## State Management

| Layer | Technology | Details |
|-------|-----------|---------|
| **Primary Store** | GitHub Issues + Labels | "Markdown as a Database" approach for distributed task state |
| **State Machine** | Label transitions | `agent:queued` → `agent:in-progress` → `agent:success` / `agent:error` |
| **Concurrency Control** | GitHub Assignees | Assign-then-verify pattern for distributed locking |
| **Audit Trail** | GitHub Issue Comments | Heartbeat updates, error logs, status transitions |

---

## Security Stack

| Mechanism | Implementation |
|-----------|---------------|
| **Webhook Verification** | HMAC SHA256 (`X-Hub-Signature-256`) |
| **Credential Scoping** | Ephemeral environment variables, destroyed on container exit |
| **Credential Scrubbing** | `scrub_secrets()` regex utility — strips `ghp_*`, `ghs_*`, `gho_*`, `github_pat_*`, `Bearer`, `sk-*` |
| **Authentication** | GitHub App Installation tokens (5,000 req/hr) |

---

## Environment Variables

### Required (3 total — per Simplification Report S-3)

| Variable | Consumer | Description |
|----------|----------|-------------|
| `*_GITHUB_TOKEN` | Both | GitHub PAT with repo permissions (prefixed: `SENTINEL_` or `NOTIFIER_`) |
| `*_GITHUB_ORG` | Both | Organization/user name |
| `*_GITHUB_REPO` | Both | Repository name |

### Optional (with sensible defaults hardcoded)

| Variable | Default | Notes |
|----------|---------|-------|
| `SENTINEL_POLL_INTERVAL_SECONDS` | 60 | Polling interval in seconds |
| `SENTINEL_MAX_CONCURRENT_TASKS` | 5 | Concurrency limit |
| `SENTINEL_HEARTBEAT_INTERVAL` | 300 | Heartbeat comment interval in seconds |
| `SENTINEL_SUBPROCESS_TIMEOUT` | 5700 | Shell-bridge timeout (95 min) |
| `SENTINEL_BOT_LOGIN` | — | Bot login for assign-then-verify locking |

---

## File Format & Configuration

| File | Format | Purpose |
|------|--------|---------|
| `pyproject.toml` | TOML | Project metadata, dependencies, ruff/mypy config |
| `uv.lock` | Lockfile | Deterministic dependency versions |
| `.env` | KEY=VALUE | Environment variables (not committed) |
| `.github/workflows/*.yml` | YAML | CI/CD pipeline definitions |
| `.opencode/agents/*.md` | Markdown | Agent definitions |
| `.opencode/commands/*.md` | Markdown | Reusable command prompts |
| `local_ai_instruction_modules/*.md` | Markdown | AI instruction modules |
