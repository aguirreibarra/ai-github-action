"""
Issue Analysis agent using OpenAI Agents SDK.
"""

from typing import List, Optional

from agents import Agent
from pydantic import BaseModel, Field

from src.tools.github_function_tools import (
    add_issue_comment,
    add_labels_to_issue,
    get_issue,
    get_repository_file_content,
    get_repository_info,
    get_repository_stats,
    list_issue_comments,
    list_issue_labels,
    list_repository_files,
    search_code,
)


class IssueCategory(BaseModel):
    """Category for an issue."""

    name: str = Field(description="The name of the category")
    confidence: float = Field(description="Confidence score (0-1)")


class IssueAnalysisResponse(BaseModel):
    """Response model for Issue Analysis agent."""

    summary: str = Field(description="A summary of the issue")
    category: IssueCategory = Field(
        description="The category of the issue (e.g., bug, feature request, question)"
    )
    complexity: str = Field(description="Estimated complexity (low, medium, high)")
    priority: str = Field(description="Suggested priority (low, medium, high)")
    related_areas: List[str] = Field(
        description="Code areas that might be related to this issue"
    )
    next_steps: List[str] = Field(
        description="Suggested next steps to resolve the issue"
    )


def create_issue_analyze_agent(
    model: str = "gpt-4o-mini", custom_prompt: Optional[str] = None
) -> Agent:
    """Create an Issue Analysis agent with issue-specific tools.

    Args:
        model: Model name to use
        custom_prompt: Custom prompt override

    Returns:
        Configured Agent instance
    """

    instructions = """
    You are an issue analyzer that helps categorize and assess GitHub issues.
    
    Your task is to investigate and analyze the issue using the tools provided and generate:
    1. A summary of the issue
    2. The category (bug, feature request, question, etc.) with confidence level
    3. Estimated complexity (low, medium, high)
    4. Suggested priority (low, medium, high)
    5. Code areas that might be related
    6. Suggested next steps
    
    Be thorough in your investigation and provide specific recommendations based on 
    the issue content and repository context.

    Use the provided tools to investigate root cause or possible solutions and provide a detailed insights.

    IMPORTANT: You MUST use the add_issue_comment tool at the end of your investigation to add a comment to the issue with your analysis.
    Call the add_labels_to_issue tool to add the appropriate labels to the issue.
    """

    if custom_prompt:
        instructions = custom_prompt

    tools = [
        get_repository_info,
        get_repository_file_content,
        get_repository_stats,
        get_issue,
        list_issue_comments,
        add_labels_to_issue,
        add_issue_comment,
        list_issue_labels,
        search_code,
        list_repository_files,
    ]

    return Agent(
        name="Issue Analysis Agent",
        instructions=instructions,
        tools=tools,
        model=model,
        output_type=IssueAnalysisResponse,
    )
