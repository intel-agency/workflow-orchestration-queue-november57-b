# Architecture — workflow-orchestration-queue (OS-APOW)

> **Source:** Synthesized from OS-APOW Architecture Guide v3.2, Development Plan v4.2, and Implementation Specification v1.2.

---

## 1. System Overview

**workflow-orchestration-queue (OS-APOW)** is a headless agentic orchestration platform that transforms GitHub Issues into automated execution orders. It moves AI from a passive co-pilot to an autonomous background production service.

The architecture follows a **4-Pillar Model** with strict separation of concerns:

```
┌──────────────────────────────────────────────────────────────────┐
│                     GITHUB (State Layer)                         │
│          Issues + Labels + Milestones + Comments                 │
│              "Markdown as a Database"                            │
└──────────┬───────────────┬───────────────────┬──────────────────┘
           │               │                   │
     ┌─────▼─────┐   ┌────▼────┐         ┌────▼────┐
     │  THE EAR  │   │  STATE  │         │  BRAIN  │
     │ (Notifier)│   │(Labels) │         │(Sentinel)│
     └─────┬─────┘   └─────────┘         └────┬────┘
           │                                   │
           │     ┌──────────────────┐          │
           └────►│  GitHub Issues   │◄─────────┘
                 │  API (REST v3)   │
                 └────────┬─────────┘
                          │
                    ┌─────▼─────┐
                    │ THE HANDS │
                    │ (Worker)  │
                    │ DevContainer
                    └───────────┘
```

---

## 2. The Four Pillars

### 2.1 The Ear (Work Event Notifier)

**File:** `src/notifier_service.py`
**Technology:** FastAPI + Uvicorn + httpx + Pydantic

The Ear is the system's sensory input — a high-performance FastAPI webhook receiver that ingests GitHub events.

**Responsibilities:**
- **Secure Webhook Ingestion:** Receives `issues`, `issue_comment`, `pull_request`, and `pull_request_review` payloads at `/webhook/github`
- **HMAC Signature Verification:** Validates `X-Hub-Signature-256` against `WEBHOOK_SECRET` to prevent spoofing
- **Intelligent Triage:** Parses issue bodies for template patterns (`[Application Plan]`, `[Bugfix]`) and auto-applies labels
- **Queue Initialization:** Applies `agent:queued` label to validated tasks via GitHub API
- **Health Monitoring:** Exposes `/health` endpoint and `/queue/status` for operational visibility

**Endpoints:**
| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/health` | Health check (returns JSON status) |
| `GET` | `/queue/status` | Queue connection status |
| `POST` | `/webhook/github` | GitHub webhook receiver |

### 2.2 The State (Work Queue)

**Implementation:** GitHub Issues + Labels + Milestones

The State pillar uses GitHub's native issue tracking as a distributed state machine. This "Markdown as a Database" approach provides:
- **World-class audit trail** — all changes are versioned and visible
- **Human supervision** — anyone can view, pause, or cancel via GitHub UI
- **Zero infrastructure** — no database to maintain or scale

**Label State Machine:**
```
agent:queued ──► agent:in-progress ──► agent:success
                       │
                       └──► agent:error
                              └──► agent:infra-failure
```

| Label | Meaning |
|-------|---------|
| `agent:queued` | Validated task awaiting a Sentinel |
| `agent:in-progress` | Sentinel has claimed the task |
| `agent:success` | Task completed successfully (PR created) |
| `agent:error` | Technical failure during execution |
| `agent:infra-failure` | Container/environment failure |
| `agent:reconciling` | Stale task being recovered (Phase 3) |

### 2.3 The Brain (Sentinel Orchestrator)

**File:** `src/orchestrator_sentinel.py`
**Technology:** Python asyncio + httpx + Docker CLI

The Brain is a persistent background daemon that polls for work, claims tasks, and manages the worker lifecycle.

**Lifecycle:**
1. **Polling Discovery** — Every 60s, queries `GET /repos/{org}/{repo}/issues?labels=agent:queued&state=open`
2. **Task Claiming** — Assign-then-verify pattern using GitHub Assignees as a distributed lock
3. **Shell-Bridge Dispatch** — Invokes `devcontainer-opencode.sh` to spawn worker containers
4. **Status Feedback** — Transitions labels, posts heartbeat comments every 5 minutes
5. **Environment Reset** — Stops worker container between tasks (stop mode)
6. **Graceful Shutdown** — Handles SIGTERM/SIGINT, finishes current task, closes connections

**Concurrency Control (Assign-then-Verify):**
```
1. POST /repos/{org}/{repo}/issues/{n}/assignees  →  assign self
2. GET  /repos/{org}/{repo}/issues/{n}             →  re-fetch issue
3. VERIFY assignees array contains SENTINEL_BOT_LOGIN
4. Only then: remove agent:queued, add agent:in-progress
```

**Resilience:**
- Jittered exponential backoff on HTTP 403/429 (max 960s)
- Subprocess timeout safety net (5700s = 95 min)
- SIGTERM/SIGINT signal handling with `_shutdown_event`

### 2.4 The Hands (Opencode Worker)

**Environment:** Docker DevContainer via `.devcontainer/`
**Runtime:** opencode CLI (v1.2.24) + LLM (GLM-5)

The Hands execute actual coding work inside an isolated DevContainer.

**Properties:**
- **High-fidelity environment** — identical to a human developer's setup
- **Resource constraints** — 2 CPUs, 4GB RAM hard cap
- **Network isolation** — cannot reach host subnet or peer containers
- **Ephemeral credentials** — tokens injected as temporary env vars, destroyed on exit
- **Instructional logic** — reads markdown modules from `local_ai_instruction_modules/`

---

## 3. Key Architectural Decisions

### ADR 07: Standardized Shell-Bridge Execution

**Decision:** The Orchestrator interacts with the worker exclusively via `./scripts/devcontainer-opencode.sh`.

**Rationale:** Reusing the shell script guarantees environment parity between AI and human developers. Reimplementing Docker orchestration in Python would cause configuration drift.

**Consequence:** Python code stays focused on logic/state. Shell scripts handle container management.

### ADR 08: Polling-First Resiliency Model

**Decision:** Polling is the primary discovery mechanism; webhooks are an optimization.

**Rationale:** Webhooks are fire-and-forget — missed events are lost. Polling ensures self-healing: upon restart, the Sentinel reconciles by looking at labels.

### ADR 09: Provider-Agnostic Interface Layer

**Decision:** Queue interactions abstracted behind an interface (Strategy Pattern).

**Rationale:** Enables future swapping of GitHub Issues for Linear, Notion, or SQL queues without rewriting orchestrator logic. The `GitHubQueue` class in `src/github_client/github_queue.py` is the current concrete implementation.

---

## 4. Data Flow (Happy Path)

```
User opens GitHub Issue
         │
         ▼
Notifier (FastAPI) receives webhook
         │
         ├──► Verify HMAC signature
         ├──► Parse issue body
         └──► Apply agent:queued label
                  │
                  ▼
Sentinel polls, discovers queued issue
         │
         ├──► Assign self (assign-then-verify)
         ├──► Remove agent:queued, add agent:in-progress
         └──► Start heartbeat coroutine
                  │
                  ▼
Sentinel dispatches via Shell Bridge
         │
         ├──► devcontainer-opencode.sh up
         ├──► devcontainer-opencode.sh start
         └──► devcontainer-opencode.sh prompt "{instruction}"
                  │
                  ▼
Worker executes in DevContainer
         │
         ├──► Clone/pull target repo
         ├──► Execute AI instruction modules
         ├──► Run tests, commit changes
         └──► Create Pull Request
                  │
                  ▼
Sentinel detects completion
         │
         ├──► Remove agent:in-progress
         ├──► Add agent:success
         ├──► Post completion comment
         └──► Stop worker container
```

---

## 5. Security Architecture

### Threat Model

| Threat | Mitigation |
|--------|-----------|
| Webhook spoofing / prompt injection | HMAC SHA256 signature verification on all incoming requests |
| Credential leakage to GitHub comments | `scrub_secrets()` regex utility strips token patterns before posting |
| Lateral movement from worker containers | Dedicated Docker bridge network, no host access |
| Resource exhaustion by rogue agent | cgroup limits: 2 CPUs, 4GB RAM per worker |
| Token persistence | Ephemeral env vars destroyed on container exit |

### Credential Scrubbing Patterns

The `scrub_secrets()` utility (in `src/models/work_item.py`) strips:
- GitHub PATs: `ghp_*`, `ghs_*`, `gho_*`, `github_pat_*`
- Bearer tokens: `Bearer ...`
- API keys: `sk-*`
- ZhipuAI keys

---

## 6. Project Structure

```
workflow-orchestration-queue/
├── pyproject.toml                    # Dependencies and metadata (uv)
├── uv.lock                           # Deterministic lockfile
├── AGENTS.md                         # AI agent instructions
├── src/
│   ├── notifier_service.py           # FastAPI webhook receiver (The Ear)
│   ├── orchestrator_sentinel.py      # Background polling daemon (The Brain)
│   ├── github_client/                # GitHub Issues API wrapper
│   │   ├── __init__.py
│   │   └── github_queue.py           # ITaskQueue ABC + GitHubQueue
│   └── models/
│       ├── __init__.py
│       └── work_item.py              # WorkItem, TaskType, WorkItemStatus, DTOs
├── tests/
│   ├── test_sentinel.py
│   ├── test_notifier.py
│   └── test_github_queue.py
├── scripts/                          # Shell bridge and utilities
├── plan_docs/                        # Planning documents
├── local_ai_instruction_modules/     # Markdown instruction modules
├── .devcontainer/                    # Consumer devcontainer
├── .github/.devcontainer/            # Build-time devcontainer
└── .github/workflows/                # CI/CD pipelines
```

---

## 7. Self-Bootstrapping Lifecycle

```
Stage 0: Developer clones template, seeds plan docs
    │
    ▼
Stage 1: Developer runs devcontainer-opencode.sh up
    │
    ▼
Stage 2: Agent runs project-setup workflow
    │         (indexes repo, configures env, validates infrastructure)
    │
    ▼
Stage 3: Developer starts sentinel.py
    │         (from this point, developer interacts ONLY via GitHub issues)
    │
    ▼
Autonomous Phase: System builds its own Phase 2 & 3 features
```

---

## 8. Cross-Cutting Concerns

| Concern | Implementation |
|---------|---------------|
| **Unified Data Model** | All models in `src/models/work_item.py` — shared by sentinel and notifier |
| **Connection Pooling** | Single `httpx.AsyncClient` per `GitHubQueue` instance, reused across calls |
| **Graceful Shutdown** | SIGTERM/SIGINT handlers set `_shutdown_event`, current task finishes before exit |
| **Environment Validation** | Both services crash at startup if required env vars are missing |
| **Logging** | Structured logging to stdout only (Docker captures via `docker logs`) |
| **Subprocess Timeout** | `asyncio.wait_for()` wrapper with 5700s ceiling for shell-bridge calls |
