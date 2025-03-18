from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError

from src.actions.code_scan import CodeScanAction
from src.github_agents.code_scan_agent import (
    CodeIssue,
    CodeScanResponse,
    create_code_scan_agent,
)


@pytest.fixture
def mock_repo_event():
    """Sample repository event data for testing."""
    return {
        "repository": {"full_name": "test-owner/test-repo"},
    }


@pytest.fixture
def mock_scan_result():
    """Mock result from Runner.run."""
    result = MagicMock()
    result.final_output = CodeScanResponse(
        overview="Test scan overview",
        issues=[
            CodeIssue(
                file="src/main.py",
                line=42,
                severity="medium",
                description="Test issue description",
                suggestion="Test suggestion",
            )
        ],
        good_practices=["Test good practice"],
        recommendations=["Test recommendation"],
    )
    return result


def test_code_issue_model():
    """Test the CodeIssue model."""
    # Test with all fields
    issue = CodeIssue(
        file="test.py",
        line=10,
        severity="high",
        description="Test description",
        suggestion="Test suggestion",
    )

    assert issue.file == "test.py"
    assert issue.line == 10
    assert issue.severity == "high"
    assert issue.description == "Test description"
    assert issue.suggestion == "Test suggestion"

    # Test with optional fields omitted
    issue_no_line = CodeIssue(
        file="test.py",
        severity="medium",
        description="No line number",
        suggestion="Test suggestion",
    )

    assert issue_no_line.file == "test.py"
    assert issue_no_line.line is None
    assert issue_no_line.severity == "medium"


def test_code_issue_validation():
    """Test CodeIssue validation."""
    # Test missing required fields
    with pytest.raises(ValidationError):
        CodeIssue(
            severity="high", description="Missing file", suggestion="Test suggestion"
        )

    with pytest.raises(ValidationError):
        CodeIssue(
            file="test.py", description="Missing severity", suggestion="Test suggestion"
        )

    with pytest.raises(ValidationError):
        CodeIssue(file="test.py", severity="high", suggestion="Missing description")

    with pytest.raises(ValidationError):
        CodeIssue(file="test.py", severity="high", description="Missing suggestion")


def test_code_scan_response_model():
    """Test the CodeScanResponse model."""
    # Create test data
    response = CodeScanResponse(
        overview="Test overview",
        issues=[
            CodeIssue(
                file="test1.py",
                line=10,
                severity="high",
                description="Issue 1",
                suggestion="Fix 1",
            ),
            CodeIssue(
                file="test2.py",
                severity="low",
                description="Issue 2",
                suggestion="Fix 2",
            ),
        ],
        good_practices=["Practice 1", "Practice 2"],
        recommendations=["Recommendation 1"],
    )

    # Verify data
    assert response.overview == "Test overview"
    assert len(response.issues) == 2
    assert response.issues[0].file == "test1.py"
    assert response.issues[1].file == "test2.py"
    assert len(response.good_practices) == 2
    assert response.good_practices[0] == "Practice 1"
    assert len(response.recommendations) == 1
    assert response.recommendations[0] == "Recommendation 1"


def test_code_scan_response_validation():
    """Test CodeScanResponse validation."""
    # Test missing required fields
    with pytest.raises(ValidationError):
        CodeScanResponse(
            issues=[],
            good_practices=[],
            recommendations=[],
            # Missing overview
        )

    with pytest.raises(ValidationError):
        CodeScanResponse(
            overview="Test overview",
            good_practices=[],
            recommendations=[],
            # Missing issues
        )

    with pytest.raises(ValidationError):
        CodeScanResponse(
            overview="Test overview",
            issues=[],
            recommendations=[],
            # Missing good_practices
        )

    with pytest.raises(ValidationError):
        CodeScanResponse(
            overview="Test overview",
            issues=[],
            good_practices=[],
            # Missing recommendations
        )


@patch("src.actions.code_scan.create_code_scan_agent")
def test_code_scan_init(mock_create_agent, mock_repo_event):
    """Test CodeScanAction initialization."""
    mock_agent = MagicMock()
    mock_create_agent.return_value = mock_agent

    action = CodeScanAction(mock_repo_event)

    assert action.event == mock_repo_event
    assert action.agent == mock_agent
    mock_create_agent.assert_called_once()


@pytest.mark.asyncio
@patch("src.actions.code_scan.logger")
@patch("src.actions.code_scan.Github")
@patch("src.actions.code_scan.GithubContext")
@patch("src.actions.code_scan.Runner")
@patch("src.actions.code_scan.create_code_scan_agent")
async def test_code_scan_run(
    mock_create_agent,
    mock_runner,
    mock_github_context,
    mock_github,
    mock_logger,
    mock_repo_event,
    mock_scan_result,
    monkeypatch,
):
    """Test CodeScanAction.run method."""
    monkeypatch.setenv("GITHUB_TOKEN", "mock-token")
    monkeypatch.setenv("MAX_TURNS", "30")

    # Setup mocks
    mock_agent = MagicMock()
    mock_create_agent.return_value = mock_agent

    mock_github_instance = MagicMock()
    mock_github.return_value = mock_github_instance

    mock_context_instance = MagicMock()
    mock_github_context.return_value = mock_context_instance

    mock_runner.run = AsyncMock(return_value=mock_scan_result)

    # Create and run the action
    action = CodeScanAction(mock_repo_event)
    await action.run()

    # Verify the correct methods were called with the right arguments
    mock_github.assert_called_once()
    mock_github_context.assert_called_once_with(
        github_event=mock_repo_event, github_client=mock_github_instance
    )

    mock_runner.run.assert_called_once()
    call_args = mock_runner.run.call_args[1]
    assert call_args["starting_agent"] == mock_agent
    assert call_args["input"] == "Please scan the repository: test-owner/test-repo\n"
    assert call_args["context"] == mock_context_instance


@pytest.mark.asyncio
@patch("src.actions.code_scan.logger")
@patch("src.actions.code_scan.create_code_scan_agent")
async def test_code_scan_run_missing_data(mock_create_agent, mock_logger):
    """Test CodeScanAction.run with missing repository data."""
    mock_agent = MagicMock()
    mock_create_agent.return_value = mock_agent

    # Create event with missing data
    event = {}  # Missing repository information

    action = CodeScanAction(event)

    with pytest.raises(ValueError, match="Missing required repository information"):
        await action.run()


@pytest.mark.asyncio
@patch("src.actions.code_scan.logger")
@patch("src.actions.code_scan.Github")
@patch("src.actions.code_scan.GithubContext")
@patch("src.actions.code_scan.Runner")
@patch("src.actions.code_scan.create_code_scan_agent")
async def test_code_scan_run_agent_exception(
    mock_create_agent,
    mock_runner,
    mock_github_context,
    mock_github,
    mock_logger,
    mock_repo_event,
    monkeypatch,
):
    """Test CodeScanAction.run with exception in Runner.run."""
    monkeypatch.setenv("GITHUB_TOKEN", "mock-token")

    # Setup mocks
    mock_agent = MagicMock()
    mock_create_agent.return_value = mock_agent

    mock_github_instance = MagicMock()
    mock_github.return_value = mock_github_instance

    mock_context_instance = MagicMock()
    mock_github_context.return_value = mock_context_instance

    # Simulate error in runner
    error_message = "Test runner error"
    mock_runner.run = AsyncMock(side_effect=Exception(error_message))

    # Create action
    action = CodeScanAction(mock_repo_event)

    # Test exception propagation
    with pytest.raises(Exception) as excinfo:
        await action.run()

    # Check the error is logged correctly
    assert str(excinfo.value) == error_message
    mock_logger.critical.assert_called_once()
    assert "Unhandled exception" in mock_logger.critical.call_args[0][0]
    # Check exc_info parameter was passed to logger
    assert mock_logger.critical.call_args[1]["exc_info"] is True


def test_create_code_scan_agent():
    """Test creation of code scan agent."""
    agent = create_code_scan_agent(model="test-model")

    assert agent.name == "Code Scan Agent"
    assert "code scan agent" in agent.instructions.lower()
    assert len(agent.tools) == 6
    assert agent.model == "test-model"
    assert agent.output_type == CodeScanResponse


def test_create_code_scan_agent_with_custom_prompt():
    """Test creation of code scan agent with custom prompt."""
    custom_prompt = "Custom test prompt"
    agent = create_code_scan_agent(model="test-model", custom_prompt=custom_prompt)

    assert agent.instructions == custom_prompt
