"""
PR Review agent using OpenAI Agents SDK.
"""

from typing import List, Optional

from agents import Agent
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
    issues: List[str] = Field(description="List of potential issues or bugs found")
    suggestions: List[str] = Field(description="List of suggestions for improvement")
    assessment: str = Field(
        description="Overall assessment (approve, request changes, comment)"
    )
    review_event: PRReviewEvent = Field(
        description="The review event type to use for the PR review"
    )


def create_pr_review_agent(
    model: str = "gpt-4o-mini", custom_prompt: Optional[str] = None
) -> Agent[PRReviewResponse]:
    """Create a PR Review agent with PR-specific tools.

    Args:
        model: Model name to use
        custom_prompt: Custom prompt override

    Returns:
        Configured Agent instance
    """

    instructions = """
    You are a reviewer who helps analyze GitHub pull requests.

    Your task is to use the tools provided to review the PR files, analyze the code changes, and provide:
    1. A summary of the changes
    2. Code quality assessment
    3. Potential issues or bugs
    4. Suggestions for improvement
    5. Overall assessment (APPROVE, REQUEST_CHANGES, COMMENT)

    Always provide constructive feedback with specific examples and suggestions.

    IMPORTANT (Follow these steps in order):
    1. You MUST use the get_pull_request tool to get information about the PR.
    2. You MUST use the get_pull_request_files tool to fetch the diff of the files in the PR.
    3. You can use the get_repository_file_content tool to get more context about the files in the PR.
    4. You can use the search_code tool to search for code in the repository.
    5. You MUST call the create_pull_request_review tool to submit your review. You're encouraged to add review_comments to the PR to help the author understand your feedback.
    """

    if custom_prompt:
        instructions = custom_prompt

    tools = [
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
