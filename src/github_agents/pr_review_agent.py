"""
PR Review agent using OpenAI Agents SDK.
"""

from agents import Agent, ComputerTool, FileSearchTool, FunctionTool, WebSearchTool
from pydantic import BaseModel, Field

from src.tools.github_function_tools import (
    PRReviewEvent,
    create_pull_request_review,
    get_pull_request,
    get_pull_request_files,
    get_repository_file_content,
    get_repository_info,
    list_repository_files,
    search_code,
)


class PRReviewResponse(BaseModel):
    """Response model for PR Review agent."""

    summary: str = Field(description="A summary of the changes in the PR")
    code_quality: str = Field(description="Assessment of code quality")
    issues: list[str] = Field(description="List of potential issues or bugs found")
    suggestions: list[str] = Field(description="List of suggestions for improvement")
    assessment: str = Field(description="Overall assessment (approve, request changes, comment)")
    review_event: PRReviewEvent = Field(
        description="The review event type to use for the PR review"
    )


def create_pr_review_agent(
    model: str = "o4-mini", custom_prompt: str | None = None
) -> Agent[PRReviewResponse]:
    """Create a PR Review agent with PR-specific tools.

    Args:
        model: Model name to use
        custom_prompt: Custom prompt override

    Returns:
        Configured Agent instance
    """

    instructions = """
    You are a code-review agent analyzing GitHub pull requests.

    Your objectives:
    - Use provided tools to gather PR data and context.
    - Identify key changes, assess quality, detect issues, and suggest improvements.
    - Deliver:
      • Summary of changes
      • Code quality assessment
      • Potential bugs or issues
      • Actionable suggestions
      • Overall recommendation: APPROVE, REQUEST_CHANGES, or COMMENT

    Workflow (follow strictly in order):
    1. get_pull_request: retrieve PR metadata
    2. get_pull_request_files: fetch changed files and diffs
    3. get_repository_file_content: get file context as needed
    4. search_code: locate related code patterns
    5. create_pull_request_review: submit review with review_comments

    Guidelines:
    - Be concise, clear, and constructive.
    - Reference code examples in feedback.
    - Explain the rationale behind each recommendation.
    """

    if custom_prompt:
        instructions = custom_prompt

    tools: list[FunctionTool | FileSearchTool | WebSearchTool | ComputerTool] = [
        get_pull_request,
        get_pull_request_files,
        get_repository_info,
        get_repository_file_content,
        search_code,
        create_pull_request_review,
        list_repository_files,
    ]

    return Agent(
        name="PR Review Agent",
        instructions=instructions,
        tools=tools,
        model=model,
        output_type=PRReviewResponse,
    )
