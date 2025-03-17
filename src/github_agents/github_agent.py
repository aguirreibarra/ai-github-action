"""
Base GitHub agent using OpenAI Agents SDK.
"""

from typing import Optional
from pydantic import BaseModel, Field
from agents import Agent

from src.tools.github_function_tools import (
    get_repository_info,
    get_repository_file_content,
    get_repository_stats,
    list_repository_files,
)


class GitHubResponse(BaseModel):
    """Response model for GitHub agent."""

    analysis: str = Field(description="The analysis or response text")
    summary: Optional[str] = Field(
        default=None, description="An optional summary of the response"
    )


def create_github_agent(
    model: str = "gpt-4o-mini", custom_prompt: Optional[str] = None
) -> Agent:
    """Create a base GitHub agent with common tools.

    Args:
        model: Model name to use
        custom_prompt: Custom prompt override

    Returns:
        Configured Agent instance
    """

    instructions = (
        "You are an AI assistant that helps with GitHub repositories. "
        "You can analyze repositories, files, and code. "
        "Provide clear, concise, and helpful responses. "
        "Always use the available tools to gather information before making judgments."
    )

    if custom_prompt:
        instructions = custom_prompt

    tools = [
        get_repository_info,
        get_repository_file_content,
        get_repository_stats,
        list_repository_files,
    ]

    return Agent(
        name="GitHub Agent",
        instructions=instructions,
        tools=tools,
        model=model,
        output_type=GitHubResponse,
    )
