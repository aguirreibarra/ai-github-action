import unittest
from unittest.mock import MagicMock, patch
import os
import sys
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from github_agent import GitHubAgent

class TestGitHubAgent(unittest.TestCase):
    def setUp(self):
        self.github_mock = MagicMock()
        self.openai_mock = MagicMock()
        
        # Apply patches
        self.github_patch = patch('github_agent.Github')
        self.openai_patch = patch('github_agent.openai')
        
        self.github_patch.start().return_value = self.github_mock
        self.openai_mock = self.openai_patch.start()
        
        # Create agent
        self.agent = GitHubAgent(
            github_token="fake-token",
            openai_api_key="fake-key",
            model="gpt-4",
            custom_prompt=None
        )
    
    def tearDown(self):
        self.github_patch.stop()
        self.openai_patch.stop()
    
    def test_initialization(self):
        # Test that the agent initializes correctly
        self.assertEqual(self.agent.github_token, "fake-token")
        self.assertEqual(self.agent.openai_api_key, "fake-key")
        self.assertEqual(self.agent.model, "gpt-4")
        self.assertIsNone(self.agent.custom_prompt)
        self.assertEqual(self.openai_mock.api_key, "fake-key")
    
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
    
    @patch('github_agent.GetPullRequestTool')
    def test_execute_tool(self, mock_tool_class):
        # Setup mock tool
        mock_tool = MagicMock()
        mock_tool.name = "get_pull_request"
        mock_tool.execute.return_value = {"title": "Test PR"}
        mock_tool_class.return_value = mock_tool
        
        # Test tool execution
        result = self.agent.execute_tool("get_pull_request", {"repo": "owner/repo", "pr_number": 123})
        
        # Check that tool was executed
        mock_tool.execute.assert_called_once_with({"repo": "owner/repo", "pr_number": 123})
        self.assertEqual(result, {"title": "Test PR"})
    
    def test_process_message(self):
        # Setup OpenAI mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = {"content": "Test response"}
        self.openai_mock.ChatCompletion.create.return_value = mock_response
        
        # Test message processing
        result = self.agent.process_message("Test message")
        
        # Check that OpenAI API was called
        self.openai_mock.ChatCompletion.create.assert_called_once()
        call_args = self.openai_mock.ChatCompletion.create.call_args[1]
        self.assertEqual(call_args["model"], "gpt-4")
        self.assertIn("messages", call_args)
        self.assertIn("tools", call_args)
        
        # Check that messages are formatted correctly
        messages = call_args["messages"]
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[-1]["role"], "user")
        self.assertEqual(messages[-1]["content"], "Test message")
        
        # Check result
        self.assertEqual(result["content"], "Test response")
        self.assertIn("conversation_history", result)
    
    def test_process_message_with_tool_calls(self):
        # Setup OpenAI mock responses for tool calling
        mock_response1 = MagicMock()
        mock_response1.choices = [MagicMock()]
        mock_message1 = {"tool_calls": [{"function": {"name": "get_pull_request", "arguments": '{}'}, "id": "call1"}]}
        mock_response1.choices[0].message = mock_message1
        
        mock_response2 = MagicMock()
        mock_response2.choices = [MagicMock()]
        mock_response2.choices[0].message = {"content": "Final response"}
        
        self.openai_mock.ChatCompletion.create.side_effect = [mock_response1, mock_response2]
        
        # Mock the execute_tool method
        self.agent.execute_tool = MagicMock(return_value={"title": "Test PR"})
        
        # Test message processing with tool calls
        result = self.agent.process_message("Test message with tool call")
        
        # Check that OpenAI API was called twice
        self.assertEqual(self.openai_mock.ChatCompletion.create.call_count, 2)
        
        # Check that tool was executed
        self.agent.execute_tool.assert_called_once_with("get_pull_request", {})
        
        # Check result
        self.assertEqual(result["content"], "Final response")
        
if __name__ == '__main__':
    unittest.main()