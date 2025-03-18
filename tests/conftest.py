import json
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up mock environment variables for testing."""
    monkeypatch.setenv("GITHUB_EVENT_PATH", "/path/to/event.json")
    monkeypatch.setenv("GITHUB_TOKEN", "mock-token")
    monkeypatch.setenv("OPENAI_API_KEY", "mock-key")
    monkeypatch.setenv("ACTION_TYPE", "pr-review")
    monkeypatch.setenv("MODEL", "gpt-4o-mini")
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("MAX_TURNS", "30")


@pytest.fixture
def mock_pr_event():
    """Return a mock PR event."""
    return {
        "action": "opened",
        "pull_request": {
            "number": 123,
            "title": "Test PR",
            "body": "Test PR body",
            "head": {"ref": "feature-branch", "sha": "abc123"},
            "base": {"ref": "main", "sha": "def456"},
        },
        "repository": {
            "full_name": "test-owner/test-repo",
            "owner": {"login": "test-owner"},
            "name": "test-repo",
        },
    }


@pytest.fixture
def mock_issue_event():
    """Return a mock issue event."""
    return {
        "action": "opened",
        "issue": {
            "number": 456,
            "title": "Test Issue",
            "body": "Test issue body",
            "user": {"login": "test-user"},
        },
        "repository": {
            "full_name": "test-owner/test-repo",
            "owner": {"login": "test-owner"},
            "name": "test-repo",
        },
    }


@pytest.fixture
def mock_github_client():
    """Return a mock Github client."""
    client = MagicMock()
    repo = MagicMock()
    client.get_repo.return_value = repo
    return client


@pytest.fixture(scope="session")
def event_file(tmpdir_factory):
    """Create a temporary event file for testing."""
    event_data = {
        "action": "opened",
        "pull_request": {"number": 123, "title": "Test PR"},
        "repository": {"full_name": "test-owner/test-repo"},
    }

    fn = tmpdir_factory.mktemp("data").join("event.json")
    with open(fn, "w") as f:
        json.dump(event_data, f)

    return str(fn)
