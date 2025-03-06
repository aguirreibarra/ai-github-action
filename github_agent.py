import json
import logging
from typing import Dict, List, Optional, Any, cast, Iterable
import openai
from openai.types.chat import ChatCompletion
from github import Github

# Define a type for OpenAI tool parameters
ChatCompletionToolParam = Dict[str, Any]

from tools.github_tools import (
    GetPullRequestTool,
    GetPullRequestFilesTool,
    GetPullRequestDiffTool,
    AddPullRequestCommentTool,
    ListPullRequestCommentsTool,
    UpdateOrCreatePullRequestCommentTool,
    GetRepositoryTool,
    GetIssueTool,
    AddIssueCommentTool,
    GetRepositoryFileContentTool,
    GetRepositoryStatsTool,
)

logger = logging.getLogger("github-agent")


class GitHubAgent:
    """Agent for interacting with GitHub repositories using OpenAI API."""

    def __init__(
        self,
        github_token: str,
        openai_api_key: str,
        model: str = "gpt-4o-mini",
        custom_prompt: Optional[str] = None,
    ):
        """Initialize the GitHub agent.

        Args:
            github_token: GitHub API token
            openai_api_key: OpenAI API key
            model: OpenAI model to use
            custom_prompt: Custom system prompt for the AI
        """
        self.github_token = github_token
        self.openai_api_key = openai_api_key
        self.model = model
        self.custom_prompt = custom_prompt

        # Initialize GitHub client
        self.github = Github(github_token)

        # Initialize OpenAI client
        self.client = openai.OpenAI(api_key=openai_api_key)

        # Register tools
        self.tools = self._register_tools()

    def _register_tools(self) -> List[ChatCompletionToolParam]:
        """Register available tools for the agent."""
        tools = [
            GetPullRequestTool(self.github),
            GetPullRequestFilesTool(self.github),
            GetPullRequestDiffTool(self.github),
            AddPullRequestCommentTool(self.github),
            ListPullRequestCommentsTool(self.github),
            UpdateOrCreatePullRequestCommentTool(self.github),
            GetRepositoryTool(self.github),
            GetIssueTool(self.github),
            AddIssueCommentTool(self.github),
            GetRepositoryFileContentTool(self.github),
            GetRepositoryStatsTool(self.github),
        ]

        # Format tools for OpenAI API and cast to the correct type
        return cast(
            List[ChatCompletionToolParam], [tool.to_openai_tool() for tool in tools]
        )

    def _get_system_prompt(self, context: Optional[str] = None) -> str:
        """Get the system prompt for the agent."""
        if self.custom_prompt:
            return self.custom_prompt

        # Default system prompt
        default_prompt = (
            "You are an AI assistant that helps with GitHub repositories. "
            "You can analyze pull requests, issues, and code. "
            "Provide clear, concise, and helpful responses. "
            "Always use the available tools to gather information before making judgments."
        )

        if context:
            default_prompt += f"\n\nContext: {context}"

        return default_prompt

    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """Execute a tool by name with the given parameters."""
        for tool in self.tools:
            if tool["function"]["name"] == tool_name:
                for original_tool in [
                    GetPullRequestTool(self.github),
                    GetPullRequestFilesTool(self.github),
                    GetPullRequestDiffTool(self.github),
                    AddPullRequestCommentTool(self.github),
                    ListPullRequestCommentsTool(self.github),
                    UpdateOrCreatePullRequestCommentTool(self.github),
                    GetRepositoryTool(self.github),
                    GetIssueTool(self.github),
                    AddIssueCommentTool(self.github),
                    GetRepositoryFileContentTool(self.github),
                    GetRepositoryStatsTool(self.github),
                ]:
                    if original_tool.name == tool_name:
                        return original_tool.execute(parameters)

        raise ValueError(f"Tool {tool_name} not found")

    def process_message(
        self,
        message: str,
        context: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        max_iterations: int = 10,
    ) -> Dict[str, Any]:
        """
        Process a user message and return a response.

        Args:
            message: The user message to process
            context: Optional context to include in the system prompt
            conversation_history: Optional conversation history
            max_iterations: Maximum number of tool calling iterations to prevent infinite loops

        Returns:
            The assistant's response
        """
        if conversation_history is None:
            conversation_history = []

        # Prepare messages
        messages = [
            {"role": "system", "content": self._get_system_prompt(context)},
            *conversation_history,
            {"role": "user", "content": message},
        ]

        # Call OpenAI API
        iteration_count = 0
        while True:
            try:
                # Check for max iterations to prevent infinite loops
                if iteration_count >= max_iterations:
                    logger.warning(
                        f"Reached maximum iterations ({max_iterations}). Breaking loop."
                    )
                    return {
                        "content": "I've reached the maximum number of operations. Please break down your request into smaller steps.",
                        "conversation_history": messages,
                    }

                iteration_count += 1

                # Call the OpenAI API with proper typing
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=self.tools,
                    tool_choice="auto",
                )

                assistant_message = response.choices[0].message
                # Convert message object to dict format for the conversation history
                assistant_dict = {
                    "role": "assistant",
                    "content": assistant_message.content,
                }

                # Add tool_calls if present
                if assistant_message.tool_calls:
                    assistant_dict["tool_calls"] = [
                        {
                            "id": tc.id,
                            "type": tc.type,
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in assistant_message.tool_calls
                    ]

                messages.append(assistant_dict)

                # Check if the assistant is requesting to use a tool
                if assistant_message.tool_calls:
                    # Execute each tool call
                    for tool_call in assistant_message.tool_calls:
                        tool_name = tool_call.function.name
                        tool_params = json.loads(tool_call.function.arguments)

                        logger.info(f"Executing tool: {tool_name}")
                        tool_result = self.execute_tool(tool_name, tool_params)

                        # Add tool result to messages
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": tool_name,
                                "content": str(tool_result),
                            }
                        )

                    # Continue the conversation with tool results
                    continue

                # Return the final response
                return {
                    "content": assistant_message.content,
                    "conversation_history": messages,
                }

            except Exception as e:
                logger.error(f"Error calling OpenAI API: {str(e)}")
                return {
                    "content": f"Error: {str(e)}",
                    "conversation_history": messages,
                }
