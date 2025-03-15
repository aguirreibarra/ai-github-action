# Tools package

import json
from typing import Any

from agents import FunctionTool, RunContextWrapper
from src.context.github_context import GithubContext
from src.tools.github_function_tools import (
    create_pull_request_review,
    get_pull_request,
    get_pull_request_files,
    get_repository_info,
    get_repository_file_content,
    list_issue_comments,
    update_or_create_pr_comment,
    add_labels_to_issue,
    add_issue_comment,
    list_issue_labels,
    search_code,
    get_issue,
    update_or_create_issue_comment,
    get_repository_stats,
    create_issue,
)

_TOOL_REGISTRY: dict[str, FunctionTool] = {
    "get_pull_request": get_pull_request,
    "get_pull_request_files": get_pull_request_files,
    "update_or_create_pr_comment": update_or_create_pr_comment,
    "get_repository_info": get_repository_info,
    "create_pull_request_review": create_pull_request_review,
    "list_issue_comments": list_issue_comments,
    "add_labels_to_issue": add_labels_to_issue,
    "add_issue_comment": add_issue_comment,
    "list_issue_labels": list_issue_labels,
    "get_repository_file_content": get_repository_file_content,
    "search_code": search_code,
    "get_issue": get_issue,
    "update_or_create_issue_comment": update_or_create_issue_comment,
    "get_repository_stats": get_repository_stats,
    "create_issue": create_issue,
}


def get_tool_by_name(name: str) -> FunctionTool | None:
    """Get a tool function by name."""
    return _TOOL_REGISTRY.get(name)


async def execute_tool(
    name: str, parameters: dict[str, Any], context: GithubContext | None = None
) -> str:
    """Execute a tool by name with the given parameters.

    Args:
        name: The name of the tool to execute
        parameters: The parameters to pass to the tool
        context: The context to pass to the tool

    Returns:
        str: The result of the tool call as a string
    """
    tool_fn = get_tool_by_name(name)
    if tool_fn is not None:
        return await tool_fn.on_invoke_tool(
            RunContextWrapper(context=context), json.dumps(parameters)
        )
    else:
        raise ValueError(f"Tool {name} not found")
