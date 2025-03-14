"""
PR Review agent using OpenAI Agents SDK.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from agents import Agent

from src.tools.github_function_tools import (
    PRReviewEvent,
    get_repository,
    get_repository_file_content,
    get_repository_stats,
    get_pull_request,
    get_pull_request_files,
    create_pull_request_review,
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
    You are a Staff Software Engineer reviewer that helps analyze GitHub pull requests.

    Your task is to use the tools provided to review the PR files, analyze the code changes, and provide:
    1. A summary of the changes
    2. Code quality assessment
    3. Potential issues or bugs
    4. Suggestions for improvement
    5. Overall assessment (APPROVE, REQUEST_CHANGES, COMMENT)

    Always provide constructive feedback with specific examples and suggestions.

    Tool Guidelines:
    - Use the appropriate tool for the task.
    - Use the get_pull_request_files tool to get the pull request files and diffs for your review.
    - You MUST call the create_pull_request_review tool to submit your review, using the review_event field value as the event parameter.
    
    Choose the appropriate review_event value for your assessment:
    - PRReviewEvent.APPROVE: For PRs that meet quality standards and have no significant issues
    - PRReviewEvent.REQUEST_CHANGES: For PRs with critical issues that must be fixed
    - PRReviewEvent.COMMENT: For PRs with minor suggestions but no blocking issues
    """

    if custom_prompt:
        instructions = custom_prompt

    tools = [
        get_repository,
        get_repository_file_content,
        get_repository_stats,
        get_pull_request,
        get_pull_request_files,
        create_pull_request_review,
    ]

    return Agent(
        name="PR Review Agent",
        instructions=instructions,
        tools=tools,
        model=model,
        output_type=PRReviewResponse,
    )
