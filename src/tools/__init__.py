# Tools package

import json
from typing import Any, Awaitable

from agents import FunctionTool, RunContextWrapper
from src.tools.github_function_tools import (
    create_pull_request_review,
    get_pull_request,
    get_pull_request_files,
    get_repository,
    update_or_create_pr_comment,
)

_TOOL_REGISTRY: dict[str, FunctionTool] = {
    "get_pull_request": get_pull_request,
    "get_pull_request_files": get_pull_request_files,
    "update_or_create_pr_comment": update_or_create_pr_comment,
    "get_repository": get_repository,
    "create_pull_request_review": create_pull_request_review,
}


def get_tool_by_name(name: str) -> FunctionTool | None:
    """Get a tool function by name."""
    return _TOOL_REGISTRY.get(name)


async def execute_tool(
    name: str, parameters: dict[str, Any], context: dict[str, Any] | None = None
) -> str:
    """Execute a tool by name with the given parameters.

    Args:
        name: The name of the tool to execute
        parameters: The parameters to pass to the tool
        context: The context to pass to the tool

    Returns:
        Awaitable[str]: The result of the tool call as a string
    """
    tool_fn = get_tool_by_name(name)
    if tool_fn is not None:
        return await tool_fn.on_invoke_tool(
            RunContextWrapper(context=context), json.dumps(parameters)
        )
    else:
        raise ValueError(f"Tool {name} not found")
