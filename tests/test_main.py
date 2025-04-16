import json
from unittest.mock import MagicMock, mock_open, patch

import pytest

from src.main import async_main, get_github_event


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up mock environment variables for testing."""
    monkeypatch.setenv("GITHUB_EVENT_PATH", "/path/to/event.json")
    monkeypatch.setenv("GITHUB_TOKEN", "mock-token")
    monkeypatch.setenv("OPENAI_API_KEY", "mock-key")
    # Don't set ACTION_TYPE here to prevent conflicts with test-specific settings


@pytest.fixture
def mock_event_data():
    """Sample GitHub event data for testing."""
    return {
        "action": "opened",
        "pull_request": {"number": 1, "title": "Test PR", "body": "Test PR body"},
    }


@patch("sys.exit")  # Patch sys.exit to prevent test from exiting
@patch("src.main.logger")  # Patch the logger to avoid logging errors
def test_get_github_event(mock_logger, mock_exit, mock_env_vars, mock_event_data):
    """Test that the get_github_event function correctly reads the event file."""
    with patch("src.main.GITHUB_EVENT_PATH", "/path/to/event.json"):
        m = mock_open(read_data=json.dumps(mock_event_data))
        with patch("builtins.open", m):
            event = get_github_event()
            assert event == mock_event_data
            m.assert_called_once_with("/path/to/event.json")


@pytest.mark.asyncio
@patch("sys.exit")
@patch("src.main.PRReviewAction")
@patch("src.main.gen_trace_id")
@patch("src.main.ACTION_TYPE", "pr-review")
async def test_async_main_pr_review(
    mock_gen_trace_id,
    mock_pr_review,
    mock_exit,
    mock_env_vars,
    mock_event_data,
):
    """Test async_main with pr-review action type."""
    mock_gen_trace_id.return_value = "test-trace-id"

    mock_action = MagicMock()
    mock_pr_review.return_value = mock_action

    m = mock_open(read_data=json.dumps(mock_event_data))
    with patch("builtins.open", m):
        await async_main()

    mock_pr_review.assert_called_once_with(mock_event_data)
    mock_action.run.assert_called_once()


@pytest.mark.asyncio
@patch("sys.exit")
@patch("src.main.IssueAnalyzeAction")
@patch("src.main.gen_trace_id")
@patch("src.main.ACTION_TYPE", "issue-analyze")
async def test_async_main_issue_analyze(
    mock_gen_trace_id,
    mock_issue_analyze,
    mock_exit,
    mock_env_vars,
    mock_event_data,
):
    """Test async_main with issue-analyze action type."""
    mock_gen_trace_id.return_value = "test-trace-id"

    mock_action = MagicMock()
    mock_issue_analyze.return_value = mock_action

    m = mock_open(read_data=json.dumps(mock_event_data))
    with patch("builtins.open", m):
        await async_main()

    mock_issue_analyze.assert_called_once_with(mock_event_data)
    mock_action.run.assert_called_once()
