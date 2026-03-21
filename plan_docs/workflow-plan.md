# Workflow Execution Plan: project-setup

**Document Type:** Workflow Execution Plan  
**Workflow:** project-setup  
**Project:** workflow-orchestration-queue (OS-APOW)  
**Repository:** intel-agency/workflow-orchestration-queue-november57-b  
**Created:** 2026-03-21  
**Status:** Approved

---

## 1. Overview

### Workflow Name
**project-setup** - Dynamic workflow for initiating a new repository and preparing it for development.

### Project Description
**workflow-orchestration-queue (OS-APOW)** is an autonomous agentic orchestration platform that transforms GitHub Issues into automated execution orders. The system moves AI from a passive co-pilot role to a background production service capable of multi-step, specification-driven task fulfillment without human intervention.

The architecture follows a 4-pillar model:
- **The Ear** (Work Event Notifier): FastAPI webhook receiver for event ingestion
- **The State** (Work Queue): GitHub Issues as distributed state management
- **The Brain** (Sentinel Orchestrator): Persistent polling and task dispatch service
- **The Hands** (Opencode Worker): Isolated DevContainer execution environment

### Total Assignments
- **Pre-script-begin:** 1 assignment
- **Main script:** 6 assignments
- **Post-assignment-complete:** 2 assignments
- **Total:** 9 assignments

---

## 2. Project Context Summary

### Key Facts from Plan Documents

#### From Development Plan v4.2
- **Phase 0 (Current):** Manual seeding from template repository
- **Phase 1 (Target):** Sentinel MVP with polling, shell-bridge execution, and status feedback
- **Phase 2 (Future):** Webhook automation (The Ear)
- **Phase 3 (Future):** Deep orchestration with Architect Sub-Agent

**Guiding Principles:**
1. Script-First Integration (use existing devcontainer-opencode.sh)
2. State Visibility & Transparency (Markdown-as-Database)
3. Self-Bootstrapping Evolution (system builds itself)
4. Resiliency through Polling (polling-first, webhooks as optimization)

#### From Architecture Guide v3.2
- **Shell-Bridge Protocol:** All orchestrator-worker communication via `./scripts/devcontainer-opencode.sh`
- **Label State Machine:** `agent:queued` → `agent:in-progress` → `agent:success` / `agent:error`
- **Concurrency Control:** Assign-then-verify pattern using GitHub Assignees
- **Security:** HMAC webhook verification, ephemeral credentials, credential scrubbing

#### From Implementation Specification v1.2
- **Project Structure:**
  ```
  workflow-orchestration-queue/
  ├── pyproject.toml
  ├── uv.lock
  ├── src/
  │   ├── notifier_service.py
  │   ├── orchestrator_sentinel.py
  │   ├── models/
  │   │   ├── work_item.py
  │   │   └── github_events.py
  │   └── queue/
  │       └── github_queue.py
  ├── scripts/
  ├── local_ai_instruction_modules/
  └── docs/
  ```
- **Required Environment Variables:** `GITHUB_TOKEN`, `GITHUB_ORG`, `GITHUB_REPO`
- **Tech Stack:** Python 3.12+, FastAPI, httpx, uv, Pydantic, Docker/DevContainers

#### From Plan Review
**Critical Issues to Address:**
- I-1: Divergent WorkItem models between components → Unified in `src/models/work_item.py`
- I-2: Race condition in task claiming → Implement assign-then-verify
- I-3: No jittered exponential backoff → Added to reference implementation
- I-6: No heartbeat implementation → Added to reference implementation

**Recommendations Implemented:**
- R-1: Heartbeat coroutine added to sentinel
- R-2: Assign-then-verify locking implemented
- R-3: Unified data model in shared module
- R-4: Graceful shutdown with signal handling

#### From Simplification Report v1
**Implemented Simplifications:**
- S-3: Reduced to 3 required env vars (GITHUB_TOKEN, GITHUB_ORG, GITHUB_REPO)
- S-4: Hardcoded ENV_RESET to "stop" mode
- S-5: Single-repo polling only (cross-repo noted as future phase)
- S-6: Consolidated queue to `src/queue/github_queue.py`
- S-7: Removed IPv4 scrubbing pattern
- S-8: Removed encryption verbiage from logs
- S-9: Phase 3 features moved to appendix
- S-10: Single logging to stdout only
- S-11: Removed unused `raw_payload` field

---

## 3. Assignment Execution Plan

### 3.1 Pre-script-begin Event

#### Assignment: create-workflow-plan
| Attribute | Value |
|-----------|-------|
| **Short ID** | create-workflow-plan |
| **Title** | Create Workflow Execution Plan |
| **Goal** | Create a comprehensive workflow execution plan document for the project-setup workflow |

**Key Acceptance Criteria:**
- [ ] Dynamic workflow file read and understood
- [ ] All workflow assignments traced and documented
- [ ] All documents in plan_docs/ read and analyzed
- [ ] Workflow execution plan produced with all required sections
- [ ] Plan saved to `plan_docs/workflow-plan.md`
- [ ] Plan committed to repository

**Project-Specific Notes:**
- This assignment is currently being executed
- Output: This document (`plan_docs/workflow-plan.md`)

**Prerequisites:** None

**Dependencies:** None

**Risks/Challenges:**
- Ensuring all plan documents are fully understood
- Capturing all project-specific context accurately

**Events:** None

---

### 3.2 Main Script Assignments

#### Assignment 1: init-existing-repository
| Attribute | Value |
|-----------|-------|
| **Short ID** | init-existing-repository |
| **Title** | Initialize Existing Repository |
| **Goal** | Initialize the existing repository environment for development |

**Key Acceptance Criteria:**
- [ ] DevContainer infrastructure validated (`.devcontainer/`, `.github/.devcontainer/`)
- [ ] All scripts functional (`devcontainer-opencode.sh`, `gh-auth.ps1`, etc.)
- [ ] Environment variables validated or placeholder identified
- [ ] Dependencies verified (Python 3.12+, uv, opencode CLI)

**Project-Specific Notes:**
- Repository is a template clone from `workflow-orchestration-queue-november57-b`
- DevContainer already configured with Dockerfile and Features
- Key scripts:
  - `scripts/devcontainer-opencode.sh` - Shell bridge to worker
  - `scripts/gh-auth.ps1` - GitHub authentication helper
  - `scripts/common-auth.ps1` - Shared auth utilities
  - `scripts/run-devcontainer-orchestrator.sh` - DevContainer orchestrator
- Required env vars to validate: `GITHUB_TOKEN`, `GITHUB_ORG`, `GITHUB_REPO`, `ZHIPU_API_KEY`

**Prerequisites:** 
- Repository cloned and accessible
- DevContainer environment available

**Dependencies:** None (first main assignment)

**Risks/Challenges:**
- Missing environment variables may require manual setup
- Template placeholders may still exist in configuration files

**Events:** None

---

#### Assignment 2: create-app-plan
| Attribute | Value |
|-----------|-------|
| **Short ID** | create-app-plan |
| **Title** | Create Application Plan |
| **Goal** | Validate and index existing plan documents, identify gaps and priorities |

**Key Acceptance Criteria:**
- [ ] All plan documents in `plan_docs/` indexed and accessible
- [ ] Key requirements extracted and prioritized
- [ ] Gaps between plan docs and reference implementations identified
- [ ] Phase 1 implementation priorities established

**Project-Specific Notes:**
- Plan documents already exist (do NOT recreate):
  - `OS-APOW Development Plan v4.2.md`
  - `OS-APOW Architecture Guide v3.2.md`
  - `OS-APOW Implementation Specification v1.2.md`
  - `OS-APOW Plan Review.md`
  - `OS-APOW Simplification Report v1.md`
- Reference implementations in `plan_docs/`:
  - `orchestrator_sentinel.py`
  - `notifier_service.py`
  - `src/models/`
  - `src/queue/`
- Focus on Phase 1 (Sentinel MVP) requirements

**Prerequisites:**
- init-existing-repository completed

**Dependencies:** 
- Requires environment validation from init-existing-repository

**Risks/Challenges:**
- Plan documents are comprehensive; need to extract actionable items
- Multiple documents have overlapping content (intentional per S-2)

**Events:** None

---

#### Assignment 3: create-project-structure
| Attribute | Value |
|-----------|-------|
| **Short ID** | create-project-structure |
| **Title** | Create Project Structure |
| **Goal** | Establish the project directory structure matching Implementation Specification |

**Key Acceptance Criteria:**
- [ ] `src/` directory created with proper structure
- [ ] `src/models/` with `__init__.py` and `work_item.py`
- [ ] `src/queue/` with `__init__.py` and `github_queue.py`
- [ ] Reference implementations moved or copied from `plan_docs/`
- [ ] `pyproject.toml` configured with dependencies

**Project-Specific Notes:**
- Target structure from Implementation Spec:
  ```
  src/
  ├── __init__.py
  ├── notifier_service.py      # From plan_docs/notifier_service.py
  ├── orchestrator_sentinel.py # From plan_docs/orchestrator_sentinel.py
  ├── models/
  │   ├── __init__.py
  │   ├── work_item.py         # From plan_docs/src/models/work_item.py
  │   └── github_events.py     # Create if needed
  └── queue/
      ├── __init__.py
      └── github_queue.py      # From plan_docs/src/queue/github_queue.py
  ```
- `scripts/` and `local_ai_instruction_modules/` already exist
- `pyproject.toml` should include: fastapi, uvicorn, httpx, pydantic

**Prerequisites:**
- create-app-plan completed (understands structure requirements)

**Dependencies:**
- Requires plan validation from create-app-plan

**Risks/Challenges:**
- Deciding whether to move or copy reference implementations
- Ensuring imports work after restructuring

**Events:** None

---

#### Assignment 4: create-repository-summary
| Attribute | Value |
|-----------|-------|
| **Short ID** | create-repository-summary |
| **Title** | Create Repository Summary |
| **Goal** | Create a comprehensive summary document of the repository |

**Key Acceptance Criteria:**
- [ ] Repository structure documented
- [ ] Key components identified and described
- [ ] Workflows documented (validate, orchestrator-agent, publish-docker, prebuild-devcontainer)
- [ ] Agent system documented (.opencode/ structure)

**Project-Specific Notes:**
- Repository is a template repo with existing infrastructure
- Key components to document:
  - `.github/workflows/` - GitHub Actions workflows
  - `.opencode/` - Agent definitions and commands
  - `.devcontainer/` - Consumer devcontainer config
  - `.github/.devcontainer/` - Build-time devcontainer
  - `scripts/` - Utility scripts
  - `local_ai_instruction_modules/` - AI instruction modules
  - `test/` - Shell-based tests
- `AGENTS.md` already contains comprehensive documentation

**Prerequisites:**
- create-project-structure completed

**Dependencies:**
- Requires actual project structure to be in place

**Risks/Challenges:**
- Avoiding duplication with existing AGENTS.md
- Ensuring summary reflects actual state, not template state

**Events:** None

---

#### Assignment 5: create-agents-md-file
| Attribute | Value |
|-----------|-------|
| **Short ID** | create-agents-md-file |
| **Title** | Create AGENTS.md File |
| **Goal** | Update AGENTS.md to reflect project-specific context |

**Key Acceptance Criteria:**
- [ ] AGENTS.md reviewed and validated
- [ ] Template placeholders updated if found
- [ ] Project-specific context added for OS-APOW
- [ ] Links and references verified

**Project-Specific Notes:**
- AGENTS.md already exists and is comprehensive
- Potential template placeholders to check:
  - `workflow-orchestration-queue-november57-b` → actual repo name
  - `intel-agency` → actual org name
- Should add OS-APOW specific context:
  - Reference to plan_docs/
  - Phase 1 implementation focus
  - Key architectural decisions

**Prerequisites:**
- create-repository-summary completed

**Dependencies:**
- Requires complete project context from previous assignments

**Risks/Challenges:**
- Template placeholders may be embedded in multiple locations
- Balancing comprehensive documentation with readability

**Events:** None

---

#### Assignment 6: debrief-and-document
| Attribute | Value |
|-----------|-------|
| **Short ID** | debrief-and-document |
| **Title** | Debrief and Document |
| **Goal** | Final documentation and handoff preparation for Phase 1 implementation |

**Key Acceptance Criteria:**
- [ ] Setup completion documented
- [ ] Any issues or warnings from setup recorded
- [ ] Phase 1 readiness checklist created
- [ ] Next steps documented

**Project-Specific Notes:**
- Document what was completed during project-setup
- Identify any configuration needed before Phase 1:
  - Environment variables to set
  - Secrets to configure
  - Services to start
- Prepare transition to Phase 1 implementation:
  - Sentinel polling service
  - GitHub label management
  - Shell-bridge execution

**Prerequisites:**
- All main script assignments completed

**Dependencies:**
- Depends on all previous main assignments

**Risks/Challenges:**
- Incomplete setup may not be discovered until Phase 1
- Environment-specific configurations may vary

**Events:** None

---

### 3.3 Post-assignment-complete Event

#### Assignment 7: validate-assignment-completion
| Attribute | Value |
|-----------|-------|
| **Short ID** | validate-assignment-completion |
| **Title** | Validate Assignment Completion |
| **Goal** | Verify all assignments completed successfully and project is ready |

**Key Acceptance Criteria:**
- [ ] All 6 main script assignments completed
- [ ] Project structure matches Implementation Specification
- [ ] `src/` directory with `models/` and `queue/` subdirectories exists
- [ ] Plan docs accessible and indexed
- [ ] AGENTS.md reflects current project state
- [ ] No template placeholders remaining in critical files

**Project-Specific Notes:**
- Validation checklist:
  - [ ] `src/notifier_service.py` exists
  - [ ] `src/orchestrator_sentinel.py` exists
  - [ ] `src/models/work_item.py` exists
  - [ ] `src/queue/github_queue.py` exists
  - [ ] `pyproject.toml` configured
  - [ ] All imports resolve correctly
  - [ ] DevContainer builds successfully

**Prerequisites:**
- All main script assignments completed

**Dependencies:**
- Depends on all main assignments

**Risks/Challenges:**
- Some validation may require runtime testing
- Import validation may need Python environment

**Events:** None

---

#### Assignment 8: report-progress
| Attribute | Value |
|-----------|-------|
| **Short ID** | report-progress |
| **Title** | Report Progress |
| **Goal** | Report workflow completion status and prepare for next phase |

**Key Acceptance Criteria:**
- [ ] Workflow completion summary generated
- [ ] Issues and warnings documented
- [ ] Phase 1 readiness status reported
- [ ] Next steps clearly communicated

**Project-Specific Notes:**
- Report should include:
  - Summary of completed assignments
  - Any issues encountered and resolutions
  - Environment configuration status
  - Phase 1 prerequisites checklist
  - Recommended next actions

**Prerequisites:**
- validate-assignment-completion completed

**Dependencies:**
- Depends on validation results

**Risks/Challenges:**
- Report may need to flag incomplete items
- Environment-specific issues may require manual intervention

**Events:** None

---

## 4. Sequencing Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PROJECT-SETUP WORKFLOW EXECUTION                          │
│                    OS-APOW: workflow-orchestration-queue                     │
└─────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
PHASE: pre-script-begin
═══════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│  [1] create-workflow-plan                                                    │
│      Creates: plan_docs/workflow-plan.md                                     │
│      Output:  This document                                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
═══════════════════════════════════════════════════════════════════════════════
PHASE: main-script (Sequential Execution)
═══════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│  [2] init-existing-repository                                                │
│      Validates: DevContainer, scripts, environment                           │
│      Checks:  GITHUB_TOKEN, GITHUB_ORG, GITHUB_REPO, ZHIPU_API_KEY          │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  [3] create-app-plan                                                         │
│      Indexes: plan_docs/*.md (5 documents)                                   │
│      Analyzes: Reference implementations in plan_docs/src/                   │
│      Output:  Phase 1 priorities and gap analysis                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  [4] create-project-structure                                                │
│      Creates:  src/ directory structure                                      │
│      Moves:    plan_docs/*.py → src/                                         │
│      Sets up:  pyproject.toml with dependencies                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  [5] create-repository-summary                                               │
│      Documents: Repository structure and components                          │
│      Reviews:  Existing AGENTS.md content                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  [6] create-agents-md-file                                                   │
│      Updates:  AGENTS.md with project-specific context                       │
│      Checks:   Template placeholders                                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  [7] debrief-and-document                                                    │
│      Creates:  Setup completion documentation                                │
│      Prepares: Phase 1 readiness checklist                                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
═══════════════════════════════════════════════════════════════════════════════
PHASE: post-assignment-complete
═══════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│  [8] validate-assignment-completion                                          │
│      Validates: All assignments completed                                    │
│      Checks:    Project structure matches spec                               │
│      Verifies:  Imports resolve, DevContainer builds                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  [9] report-progress                                                         │
│      Outputs:  Workflow completion summary                                   │
│      Flags:    Issues, warnings, Phase 1 readiness                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
                           ╔═══════════════════╗
                           ║  WORKFLOW COMPLETE ║
                           ║  Ready for Phase 1 ║
                           ╚═══════════════════╝

═══════════════════════════════════════════════════════════════════════════════
DEPENDENCY CHAIN
═══════════════════════════════════════════════════════════════════════════════

  create-workflow-plan
         │
         ▼
  init-existing-repository ─────────────────────────────────────┐
         │                                                      │
         ▼                                                      │
  create-app-plan ◄─────────────────────────────────────────────┤
         │                                                      │
         ▼                                                      │
  create-project-structure ◄────────────────────────────────────┤ (structure needs)
         │                                                      │
         ▼                                                      │
  create-repository-summary ◄───────────────────────────────────┤ (context needs)
         │                                                      │
         ▼                                                      │
  create-agents-md-file ◄───────────────────────────────────────┤ (full context)
         │                                                      │
         ▼                                                      │
  debrief-and-document ◄────────────────────────────────────────┘
         │
         ▼
  validate-assignment-completion
         │
         ▼
  report-progress
```

---

## 5. Open Questions

### 5.1 Implementation Questions

| # | Question | Impact | Recommendation |
|---|----------|--------|----------------|
| 1 | Should reference implementations be **moved** from `plan_docs/` to `src/` or **copied**? | Medium | **Move** - keeps single source of truth, plan_docs can reference src/ |
| 2 | Should `github_events.py` be created in `src/models/`? | Low | **Yes** - Notifier needs it for webhook payload parsing |
| 3 | Should `pyproject.toml` be created or does one exist? | High | **Verify** - Check if template includes pyproject.toml |
| 4 | What is the target Python version for pyproject.toml? | Medium | **3.12+** - Per Implementation Specification |

### 5.2 Environment Questions

| # | Question | Impact | Recommendation |
|---|----------|--------|----------------|
| 5 | Are all required environment variables already set? | High | **Validate** during init-existing-repository |
| 6 | Should `.env.example` be created for reference? | Low | **Yes** - Helps with onboarding |
| 7 | Is `SENTINEL_BOT_LOGIN` required for Phase 0? | Medium | **No** - Only needed when multiple sentinels run (Phase 1+) |

### 5.3 Documentation Questions

| # | Question | Impact | Recommendation |
|---|----------|--------|----------------|
| 8 | Should AGENTS.md be extensively modified or lightly updated? | Medium | **Light update** - Existing content is comprehensive |
| 9 | Should a separate `docs/setup.md` be created? | Low | **Optional** - AGENTS.md may be sufficient |
| 10 | Should Phase 1 stories be created as GitHub Issues? | Medium | **Yes** - Enables self-bootstrapping workflow |

---

## 6. Risk Register

| Risk ID | Risk Description | Probability | Impact | Mitigation |
|---------|------------------|-------------|--------|------------|
| R-001 | Template placeholders remain in configuration files | Medium | High | Automated search for template strings during validation |
| R-002 | Missing environment variables block setup | Medium | High | Early validation with clear error messages |
| R-003 | Import errors after restructuring | Low | Medium | Run Python import validation during create-project-structure |
| R-004 | DevContainer build failures | Low | High | Test build during init-existing-repository |
| R-005 | Divergence between plan docs and reference implementations | Low | Medium | Cross-reference during create-app-plan |

---

## 7. Acceptance Criteria Summary

### Workflow-Level Acceptance

- [ ] All 9 assignments completed successfully
- [ ] Project structure matches Implementation Specification
- [ ] Reference implementations accessible in `src/`
- [ ] Plan documents indexed and gaps identified
- [ ] AGENTS.md reflects current project state
- [ ] Phase 1 readiness checklist available
- [ ] No blocking issues remaining

### Deliverables

| Deliverable | Location | Status |
|-------------|----------|--------|
| Workflow Execution Plan | `plan_docs/workflow-plan.md` | ✅ Complete |
| Project Structure | `src/` | ⏳ Pending |
| Repository Summary | Documentation | ⏳ Pending |
| Updated AGENTS.md | `AGENTS.md` | ⏳ Pending |
| Phase 1 Readiness | Documentation | ⏳ Pending |

---

## 8. Next Steps After Workflow Completion

1. **Environment Setup**
   - Configure `GITHUB_TOKEN`, `GITHUB_ORG`, `GITHUB_REPO` environment variables
   - Set `ZHIPU_API_KEY` for opencode CLI
   - Configure `WEBHOOK_SECRET` for notifier service

2. **Phase 1 Implementation**
   - Create GitHub Issues for Phase 1 user stories
   - Implement Sentinel polling service
   - Implement Notifier webhook receiver
   - Test shell-bridge integration

3. **Validation**
   - Run test suites: `bash test/test-devcontainer-build.sh`
   - Validate DevContainer: `./scripts/devcontainer-opencode.sh up`
   - Test opencode integration: `opencode --version`

---

*This workflow execution plan was generated as part of the project-setup dynamic workflow.*
