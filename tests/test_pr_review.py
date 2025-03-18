from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.actions.pr_review import PRReviewAction


@pytest.fixture
def mock_event():
    """Sample PR event data for testing."""
    return {
        "pull_request": {"number": 123},
        "repository": {"full_name": "test-owner/test-repo"},
    }


@pytest.fixture
def mock_result():
    """Mock result from Runner.run."""
    result = MagicMock()
    result.final_output = "PR review completed successfully"
    return result


@patch("src.actions.pr_review.create_pr_review_agent")
def test_pr_review_init(mock_create_agent, mock_event):
    """Test PRReviewAction initialization."""
    mock_agent = MagicMock()
    mock_create_agent.return_value = mock_agent

    action = PRReviewAction(mock_event)

    assert action.event == mock_event
    assert action.agent == mock_agent
    mock_create_agent.assert_called_once()


@pytest.mark.asyncio
@patch("sys.exit")
@patch("src.actions.pr_review.logger")
@patch("src.actions.pr_review.Github")
@patch("src.actions.pr_review.GithubContext")
@patch("src.actions.pr_review.Runner")
@patch("src.actions.pr_review.create_pr_review_agent")
async def test_pr_review_run(
    mock_create_agent,
    mock_runner,
    mock_github_context,
    mock_github,
    mock_logger,
    mock_exit,
    mock_event,
    mock_result,
    monkeypatch,
):
    """Test PRReviewAction.run method."""
    monkeypatch.setenv("GITHUB_TOKEN", "mock-token")
    monkeypatch.setenv("MAX_TURNS", "30")

    # Setup mocks
    mock_agent = MagicMock()
    mock_create_agent.return_value = mock_agent

    mock_github_instance = MagicMock()
    mock_github.return_value = mock_github_instance

    mock_context_instance = MagicMock()
    mock_github_context.return_value = mock_context_instance

    mock_runner.run = AsyncMock(return_value=mock_result)

    # Create and run the action
    action = PRReviewAction(mock_event)
    await action.run()

    # Verify the correct methods were called with the right arguments
    mock_github.assert_called_once()
    mock_github_context.assert_called_once_with(
        github_event=mock_event, github_client=mock_github_instance
    )

    mock_runner.run.assert_called_once()
    call_args = mock_runner.run.call_args[1]
    assert call_args["starting_agent"] == mock_agent
    assert call_args["input"] == "Pull request review for test-owner/test-repo#123"
    assert call_args["context"] == mock_context_instance


@pytest.mark.asyncio
@patch("sys.exit")
@patch("src.actions.pr_review.logger")
@patch("src.actions.pr_review.create_pr_review_agent")
async def test_pr_review_run_missing_data(mock_create_agent, mock_logger, mock_exit):
    """Test PRReviewAction.run with missing PR data."""
    mock_agent = MagicMock()
    mock_create_agent.return_value = mock_agent

    # Create event with missing data
    event = {
        "pull_request": {},  # Missing number
        "repository": {"full_name": "test-owner/test-repo"},
    }

    action = PRReviewAction(event)

    with pytest.raises(ValueError, match="Missing required PR information"):
        await action.run()
