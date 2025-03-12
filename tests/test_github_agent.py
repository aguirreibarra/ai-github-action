import unittest
from unittest.mock import MagicMock, patch
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.github_agent import GitHubAgent


class TestGitHubAgent(unittest.TestCase):
    def setUp(self):
        self.github_mock = MagicMock()
        self.openai_client_mock = MagicMock()

        # Apply patches
        self.github_patch = patch("src.github_agent.Github")
        self.openai_patch = patch("src.github_agent.openai")

        self.github_patch.start().return_value = self.github_mock
        self.openai_mock = self.openai_patch.start()
        self.openai_mock.OpenAI.return_value = self.openai_client_mock

        # Create agent
        self.agent = GitHubAgent(
            github_token="fake-token",
            openai_api_key="fake-key",
            model="gpt-4",
            custom_prompt=None,
        )

        # Ensure the agent has tool implementations initialized
        self.agent._register_tools()

        # Assign the client directly to ensure it's accessible in tests
        self.agent.client = self.openai_client_mock

    def tearDown(self):
        self.github_patch.stop()
        self.openai_patch.stop()

    def test_initialization(self):
        # Test that the agent initializes correctly
        self.assertEqual(self.agent.github_token, "fake-token")
        self.assertEqual(self.agent.openai_api_key, "fake-key")
        self.assertEqual(self.agent.model, "gpt-4")
        self.assertIsNone(self.agent.custom_prompt)
        # In new code we use client object instead of global API key
        self.openai_mock.OpenAI.assert_called_once_with(api_key="fake-key")

    def test_register_tools(self):
        # Test that tools are registered correctly
        tools = self.agent._register_tools()

        # Check if tools are registered
        self.assertIsInstance(tools, list)
        self.assertGreater(len(tools), 0)

        # Check tool format
        for tool in tools:
            self.assertIn("type", tool)
            self.assertIn("function", tool)
            self.assertIn("name", tool["function"])
            self.assertIn("description", tool["function"])
            self.assertIn("parameters", tool["function"])

    def test_get_system_prompt(self):
        # Test default prompt
        default_prompt = self.agent._get_system_prompt()
        self.assertIn("GitHub", default_prompt)

        # Test with context
        context_prompt = self.agent._get_system_prompt("Test Context")
        self.assertIn("Test Context", context_prompt)

        # Test with custom prompt
        self.agent.custom_prompt = "Custom prompt"
        custom_prompt = self.agent._get_system_prompt()
        self.assertEqual(custom_prompt, "Custom prompt")

    @patch("src.github_agent.GetPullRequestTool")
    def test_execute_tool(self, mock_tool_class):
        # Setup mock tool
        mock_tool = MagicMock()
        mock_tool.name = "get_pull_request"
        mock_tool.execute.return_value = {"title": "Test PR"}
        mock_tool_class.return_value = mock_tool

        # Create a new tools list with only our mock tool
        self.agent._tool_implementations = [mock_tool]
        self.agent.tools = [
            {"type": "function", "function": {"name": "get_pull_request"}}
        ]

        # Test tool execution
        result = self.agent.execute_tool(
            "get_pull_request", {"repo": "owner/repo", "pr_number": 123}
        )

        # Check that tool was executed
        mock_tool.execute.assert_called_once_with(
            {"repo": "owner/repo", "pr_number": 123}
        )
        self.assertEqual(result, {"title": "Test PR"})

    def test_process_message(self):
        # Setup OpenAI mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        # Create a response object with content attribute
        mock_message = MagicMock()
        mock_message.content = "Test response"
        mock_message.tool_calls = None
        mock_response.choices[0].message = mock_message

        # Use side_effect to capture the messages at the time of the API call
        original_messages = None

        def capture_messages_side_effect(**kwargs):
            nonlocal original_messages
            original_messages = kwargs["messages"].copy()
            return mock_response

        self.openai_client_mock.chat.completions.create.side_effect = (
            capture_messages_side_effect
        )

        # Test message processing with explicit max_iterations
        result = self.agent.process_message("Test message", max_iterations=5)

        # Check that OpenAI API was called
        self.openai_client_mock.chat.completions.create.assert_called_once()
        call_args = self.openai_client_mock.chat.completions.create.call_args[1]
        self.assertEqual(call_args["model"], "gpt-4")
        self.assertIn("messages", call_args)
        self.assertIn("tools", call_args)

        # Check that initial messages sent to API are formatted correctly
        self.assertEqual(original_messages[0]["role"], "system")
        self.assertEqual(original_messages[-1]["role"], "user")
        self.assertEqual(original_messages[-1]["content"], "Test message")

        # Check result
        self.assertEqual(result["content"], "Test response")
        self.assertIn("conversation_history", result)

        # Final conversation history should include the response
        conversation_history = result["conversation_history"]
        self.assertEqual(conversation_history[-1]["role"], "assistant")
        self.assertEqual(conversation_history[-1]["content"], "Test response")

    def test_process_message_with_tool_calls(self):
        """Test that the agent correctly processes a message with tool calls."""
        # Setup OpenAI mock responses for tool calling
        mock_response1 = MagicMock()
        mock_response1.choices = [MagicMock()]

        # Create a tool call object
        mock_tool_call = MagicMock()
        mock_tool_call.id = "call1"
        mock_tool_call.type = "function"
        mock_tool_call.function = MagicMock()
        mock_tool_call.function.name = "get_pull_request"
        mock_tool_call.function.arguments = "{}"

        # Create a message with tool calls
        mock_message1 = MagicMock()
        mock_message1.tool_calls = [mock_tool_call]
        mock_message1.content = None
        mock_response1.choices[0].message = mock_message1

        # Create a final response message
        mock_response2 = MagicMock()
        mock_response2.choices = [MagicMock()]
        mock_message2 = MagicMock()
        mock_message2.content = "Final response"
        mock_message2.tool_calls = None
        mock_response2.choices[0].message = mock_message2

        # Reset mock to clear history and configure it
        self.openai_client_mock.chat.completions.create.reset_mock()
        self.openai_client_mock.chat.completions.create.side_effect = [
            mock_response1,
            mock_response2,
        ]

        # Mock the execute_tool method
        self.agent.execute_tool = MagicMock(return_value={"title": "Test PR"})

        # Test message processing with tool calls
        result = self.agent.process_message(
            "Test message with tool call", max_iterations=3
        )

        # Verify API was called twice (once for tool call, once for final response)
        self.assertEqual(self.openai_client_mock.chat.completions.create.call_count, 2)

        # Verify we got the expected result
        self.assertEqual(result["content"], "Final response")

        # Check that tool was executed
        self.agent.execute_tool.assert_called_once_with("get_pull_request", {})

    def test_process_message_max_iterations(self):
        """Test that process_message respects the max_iterations parameter."""
        # Create an infinite loop scenario with tool calls that never resolve
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]

        # Create a tool call that would keep calling in a loop
        mock_tool_call = MagicMock()
        mock_tool_call.id = "call1"
        mock_tool_call.type = "function"
        mock_tool_call.function = MagicMock()
        mock_tool_call.function.name = "get_pull_request"
        mock_tool_call.function.arguments = "{}"

        mock_message = MagicMock()
        mock_message.tool_calls = [mock_tool_call]
        mock_message.content = None
        mock_response.choices[0].message = mock_message

        # Reset any previous mock configuration
        self.openai_client_mock.chat.completions.create.reset_mock()
        self.openai_client_mock.chat.completions.create.return_value = mock_response

        # Mock the execute_tool method to return a valid result
        self.agent.execute_tool = MagicMock(return_value={"title": "Test PR"})

        # Test with max_iterations=2
        result = self.agent.process_message("Test message", max_iterations=2)

        # Check that API was called exactly max_iterations times
        self.assertEqual(self.openai_client_mock.chat.completions.create.call_count, 2)

        # Should include a message about reaching max iterations
        self.assertIn("maximum number of operations", result["content"])

        # Verify we got a proper result structure
        self.assertIn("conversation_history", result)


if __name__ == "__main__":
    unittest.main()
