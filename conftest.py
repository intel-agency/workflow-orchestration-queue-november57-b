"""Pytest configuration and fixtures."""

import sys
from pathlib import Path

import pytest

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


@pytest.fixture
def mock_github_token() -> str:
    """Provide a mock GitHub token for testing."""
    return "ghp_test_token_12345"


@pytest.fixture
def mock_github_org() -> str:
    """Provide a mock GitHub organization for testing."""
    return "test-org"


@pytest.fixture
def mock_github_repo() -> str:
    """Provide a mock GitHub repository for testing."""
    return "test-repo"
