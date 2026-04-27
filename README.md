# Workflow Orchestration Queue (OS-APOW)

A Python-based workflow orchestration system that uses GitHub Issues as a task queue, featuring a Sentinel background service for processing and a Notifier FastAPI service for webhook reception.

## Overview

This project implements a distributed task queue using GitHub Issues as the backing store:

- **Notifier Service**: FastAPI application that receives GitHub webhooks and creates work items
- **Sentinel Service**: Background daemon that processes queued work items
- **GitHub Issues**: Acts as the persistent task queue with labels for status tracking

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   GitHub Event  │────▶│    Notifier     │────▶│  GitHub Issues  │
│    Webhook      │     │    Service      │     │   (Queue)       │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                                                         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Processed     │◀────│    Sentinel     │◀────│   Work Items    │
│     Tasks       │     │    Service      │     │   (Queued)      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Features

- GitHub Issues as task queue with label-based status tracking
- FastAPI webhook receiver for GitHub events
- Async background processing with configurable concurrency
- Health check endpoints for monitoring
- Docker support for containerized deployment
- Type-safe with Pydantic models

## Quick Start

### Prerequisites

- Python 3.12+
- UV package manager
- Docker (optional)

### Installation

```bash
# Clone the repository
git clone https://github.com/intel-agency/workflow-orchestration-queue-november57-b.git
cd workflow-orchestration-queue-november57-b

# Install dependencies
uv sync

# Run tests
uv run pytest

# Run linter
uv run ruff check src/
```

### Running Services

#### Local Development

```bash
# Set environment variables
export NOTIFIER_GITHUB_TOKEN="your-github-token"
export NOTIFIER_GITHUB_ORG="your-org"
export NOTIFIER_GITHUB_REPO="your-repo"

# Run the notifier service
uv run uvicorn notifier_service:app --reload --port 8000

# In another terminal, run the sentinel
export SENTINEL_GITHUB_TOKEN="your-github-token"
export SENTINEL_GITHUB_ORG="your-org"
export SENTINEL_GITHUB_REPO="your-repo"
uv run python -m orchestrator_sentinel
```

#### Docker

```bash
# Build and run with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Project Structure

```
/
├── src/
│   ├── orchestrator_sentinel.py    # Main Sentinel background service
│   ├── notifier_service.py         # FastAPI webhook receiver
│   ├── github_client/              # Was queue/ - renamed per S-6
│   │   ├── __init__.py
│   │   └── github_queue.py         # GitHub Issues API wrapper
│   └── models/
│       ├── __init__.py
│       └── work_item.py            # WorkItem, TaskType, WorkItemStatus models
├── tests/
│   ├── __init__.py
│   ├── test_sentinel.py
│   ├── test_notifier.py
│   └── test_github_queue.py
├── docs/                           # Documentation
├── scripts/                        # Utility scripts
├── plan_docs/                      # Project planning documents
├── pyproject.toml                  # UV project configuration
├── Dockerfile                      # Container image definition
└── docker-compose.yml              # Local development orchestration
```

## Configuration

### Environment Variables

#### Notifier Service

| Variable | Description | Required |
|----------|-------------|----------|
| `NOTIFIER_GITHUB_TOKEN` | GitHub personal access token | Yes |
| `NOTIFIER_GITHUB_ORG` | GitHub organization/user | Yes |
| `NOTIFIER_GITHUB_REPO` | Repository name | Yes |

#### Sentinel Service

| Variable | Description | Default |
|----------|-------------|---------|
| `SENTINEL_GITHUB_TOKEN` | GitHub personal access token | Required |
| `SENTINEL_GITHUB_ORG` | GitHub organization/user | Required |
| `SENTINEL_GITHUB_REPO` | Repository name | Required |
| `SENTINEL_POLL_INTERVAL_SECONDS` | Queue polling interval | 60 |
| `SENTINEL_MAX_CONCURRENT_TASKS` | Max concurrent tasks | 5 |
| `SENTINEL_QUEUE_LABELS` | Labels for queued items | `["queued"]` |

## API Endpoints

### Notifier Service

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/queue/status` | GET | Queue connection status |
| `/webhook/github` | POST | GitHub webhook receiver |

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src

# Run specific test file
uv run pytest tests/test_notifier.py -v
```

### Code Quality

```bash
# Lint with ruff
uv run ruff check src/

# Format with ruff
uv run ruff format src/

# Type check with mypy
uv run mypy src/
```

## License

MIT License - See [LICENSE](LICENSE) for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linters
5. Submit a pull request
