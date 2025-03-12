"""
PR Review agent using OpenAI Agents SDK.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from agents import Agent

from src.tools.github_function_tools import (
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
    approval_recommendation: bool = Field(description="Should this PR be approved?")


def create_pr_review_agent(
    model: str = "gpt-4o-mini", custom_prompt: Optional[str] = None
) -> Agent[PRReviewResponse]:
    """Create a PR Review agent with PR-specific tools.

    Args:
        github_client: GitHub client
        model: Model name to use
        custom_prompt: Custom prompt override

    Returns:
        Configured Agent instance
    """

    instructions = """
    You are a Staff Software Engineer reviewer that helps analyze GitHub pull requests.

    Your task is to review the PR files, analyze the code changes, and provide:
    1. A summary of the changes
    2. Code quality assessment
    3. Potential issues or bugs
    4. Suggestions for improvement
    5. Overall assessment (approve, request changes, comment)

    Always provide constructive feedback with specific examples and suggestions.

    Explicitly call the create_pull_request_review tool with your assessment. 
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
