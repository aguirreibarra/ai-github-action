import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from src.actions.issue_analyze import IssueAnalyzeAction


@pytest.fixture
def mock_event():
    """Sample issue event data for testing."""
    return {
        "issue": {"number": 456},
        "repository": {"full_name": "test-owner/test-repo"},
    }


@pytest.fixture
def mock_result():
    """Mock result from Runner.run."""
    result = MagicMock()
    result.final_output = "Issue analysis completed successfully"
    return result


@patch("src.actions.issue_analyze.create_issue_analyze_agent")
def test_issue_analyze_init(mock_create_agent, mock_event):
    """Test IssueAnalyzeAction initialization."""
    mock_agent = MagicMock()
    mock_create_agent.return_value = mock_agent

    action = IssueAnalyzeAction(mock_event)

    assert action.event == mock_event
    assert action.agent == mock_agent
    mock_create_agent.assert_called_once_with(model="gpt-4o-mini", custom_prompt=None)


@pytest.mark.asyncio
@patch("src.actions.issue_analyze.logger")
@patch("src.actions.issue_analyze.Github")
@patch("src.actions.issue_analyze.GithubContext")
@patch("src.actions.issue_analyze.Runner")
@patch("src.actions.issue_analyze.create_issue_analyze_agent")
@patch("src.actions.issue_analyze.GITHUB_TOKEN", "mock-token")
@patch("src.actions.issue_analyze.MAX_TURNS", 30)
async def test_issue_analyze_run(
    mock_create_agent,
    mock_runner,
    mock_github_context,
    mock_github,
    mock_logger,
    mock_event,
    mock_result,
):
    """Test IssueAnalyzeAction.run method."""
    # Setup mocks
    mock_agent = MagicMock()
    mock_create_agent.return_value = mock_agent

    mock_github_instance = MagicMock()
    mock_github.return_value = mock_github_instance

    mock_context_instance = MagicMock()
    mock_github_context.return_value = mock_context_instance

    mock_runner.run = AsyncMock(return_value=mock_result)

    # Create and run the action
    action = IssueAnalyzeAction(mock_event)
    await action.run()

    # Verify the correct methods were called with the right arguments
    mock_github.assert_called_once_with("mock-token")
    mock_github_context.assert_called_once_with(
        github_event=mock_event, github_client=mock_github_instance
    )

    mock_runner.run.assert_called_once()
    call_args = mock_runner.run.call_args[1]
    assert call_args["starting_agent"] == mock_agent
    assert "Please analyze this GitHub issue" in call_args["input"]
    assert "Repository: test-owner/test-repo" in call_args["input"]
    assert "Issue #456" in call_args["input"]
    assert call_args["context"] == mock_context_instance
    assert call_args["max_turns"] == 30


@pytest.mark.asyncio
@patch("src.actions.issue_analyze.logger")
@patch("src.actions.issue_analyze.create_issue_analyze_agent")
async def test_issue_analyze_run_missing_data(mock_create_agent, mock_logger):
    """Test IssueAnalyzeAction.run with missing issue data."""
    mock_agent = MagicMock()
    mock_create_agent.return_value = mock_agent

    # Create event with missing data
    event = {
        "issue": {},  # Missing number
        "repository": {"full_name": "test-owner/test-repo"},
    }

    action = IssueAnalyzeAction(event)

    with pytest.raises(ValueError, match="Missing required issue information"):
        await action.run()


@pytest.mark.asyncio
@patch("src.actions.issue_analyze.logger")
@patch("src.actions.issue_analyze.create_issue_analyze_agent")
async def test_issue_analyze_run_exception(mock_create_agent, mock_logger):
    """Test IssueAnalyzeAction.run with an exception during processing."""
    mock_agent = MagicMock()
    mock_create_agent.return_value = mock_agent

    # Valid event
    event = {
        "issue": {"number": 456},
        "repository": {"full_name": "test-owner/test-repo"},
    }

    action = IssueAnalyzeAction(event)

    # Simulate an exception during processing
    with patch("src.actions.issue_analyze.Runner.run") as mock_run:
        mock_run.side_effect = Exception("Test exception")

        with pytest.raises(Exception, match="Test exception"):
            await action.run()

        # Verify error was logged
        mock_logger.critical.assert_called_once()
