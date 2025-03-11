import unittest
from unittest.mock import MagicMock
import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
)


class TestGitHubTools(unittest.TestCase):
    def setUp(self):
        self.github_mock = MagicMock()
        self.repo_mock = MagicMock()
        self.pr_mock = MagicMock()
        self.issue_mock = MagicMock()
        self.file_mock = MagicMock()
        self.comment_mock = MagicMock()

        # Configure mocks
        self.github_mock.get_repo.return_value = self.repo_mock
        self.repo_mock.get_pull.return_value = self.pr_mock
        self.repo_mock.get_issue.return_value = self.issue_mock
        self.pr_mock.get_files.return_value = [self.file_mock]
        self.pr_mock.create_issue_comment.return_value = self.comment_mock
        self.issue_mock.create_comment.return_value = self.comment_mock

        # Set up mock attributes
        self.pr_mock.number = 123
        self.pr_mock.title = "Test PR"
        self.pr_mock.body = "Test PR description"
        self.pr_mock.state = "open"
        self.pr_mock.user.login = "testuser"
        self.pr_mock.created_at.isoformat.return_value = "2023-01-01T00:00:00Z"
        self.pr_mock.updated_at.isoformat.return_value = "2023-01-02T00:00:00Z"
        self.pr_mock.merged = False
        self.pr_mock.mergeable = True
        self.pr_mock.comments = 0
        self.pr_mock.commits = 1
        self.pr_mock.additions = 10
        self.pr_mock.deletions = 5
        self.pr_mock.changed_files = 2

        self.file_mock.filename = "test.py"
        self.file_mock.status = "modified"
        self.file_mock.additions = 10
        self.file_mock.deletions = 5
        self.file_mock.changes = 15
        self.file_mock.blob_url = "https://github.com/owner/repo/blob/test.py"
        self.file_mock.raw_url = "https://github.com/owner/repo/raw/test.py"
        self.file_mock.patch = "@@ -1,5 +1,10 @@\n+# New line\n def test():\n-    return 'old'\n+    return 'new'\n"

        self.issue_mock.number = 123
        self.issue_mock.title = "Test Issue"
        self.issue_mock.body = "Test issue description"
        self.issue_mock.state = "open"
        self.issue_mock.user.login = "testuser"
        self.issue_mock.created_at.isoformat.return_value = "2023-01-01T00:00:00Z"
        self.issue_mock.updated_at.isoformat.return_value = "2023-01-02T00:00:00Z"
        self.issue_mock.comments = 0
        self.issue_mock.labels = []
        self.issue_mock.assignees = []

        self.comment_mock.id = 456
        self.comment_mock.html_url = (
            "https://github.com/owner/repo/pull/123#issuecomment-456"
        )

    def test_get_pull_request_tool(self):
        tool = GetPullRequestTool(self.github_mock)

        # Test tool properties
        self.assertEqual(tool.name, "get_pull_request")
        self.assertTrue("pull request" in tool.description.lower())
        self.assertIn("repo", tool.parameters)
        self.assertIn("pr_number", tool.parameters)

        # Test OpenAI tool format
        openai_tool = tool.to_openai_tool()
        self.assertEqual(openai_tool["function"]["name"], "get_pull_request")

        # Test execution
        result = tool.execute({"repo": "owner/repo", "pr_number": 123})

        self.github_mock.get_repo.assert_called_once_with("owner/repo")
        self.repo_mock.get_pull.assert_called_once_with(123)

        self.assertEqual(result["number"], 123)
        self.assertEqual(result["title"], "Test PR")
        self.assertEqual(result["body"], "Test PR description")
        self.assertEqual(result["state"], "open")

    def test_get_pull_request_files_tool(self):
        tool = GetPullRequestFilesTool(self.github_mock)

        result = tool.execute({"repo": "owner/repo", "pr_number": 123})

        self.github_mock.get_repo.assert_called_once_with("owner/repo")
        self.repo_mock.get_pull.assert_called_once_with(123)
        self.pr_mock.get_files.assert_called_once()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["filename"], "test.py")
        self.assertEqual(result[0]["status"], "modified")
        self.assertEqual(result[0]["additions"], 10)

    def test_get_pull_request_diff_tool(self):
        tool = GetPullRequestDiffTool(self.github_mock)

        result = tool.execute(
            {"repo": "owner/repo", "pr_number": 123, "filename": "test.py"}
        )

        self.github_mock.get_repo.assert_called_once_with("owner/repo")
        self.repo_mock.get_pull.assert_called_once_with(123)
        self.pr_mock.get_files.assert_called_once()

        self.assertEqual(
            result,
            "@@ -1,5 +1,10 @@\n+# New line\n def test():\n-    return 'old'\n+    return 'new'\n",
        )

    def test_add_pull_request_comment_tool(self):
        tool = AddPullRequestCommentTool(self.github_mock)

        result = tool.execute(
            {"repo": "owner/repo", "pr_number": 123, "body": "This is a test comment"}
        )

        self.github_mock.get_repo.assert_called_once_with("owner/repo")
        self.repo_mock.get_pull.assert_called_once_with(123)
        self.pr_mock.create_issue_comment.assert_called_once_with(
            "This is a test comment"
        )

        self.assertEqual(result["id"], 456)
        self.assertEqual(
            result["url"], "https://github.com/owner/repo/pull/123#issuecomment-456"
        )

    def test_list_pull_request_comments_tool(self):
        tool = ListPullRequestCommentsTool(self.github_mock)

        # Set up mock for get_issue_comments
        comment1 = MagicMock()
        comment1.id = 111
        comment1.body = "First comment"
        comment1.user.login = "user1"
        comment1.created_at = datetime(2023, 1, 1)
        comment1.updated_at = datetime(2023, 1, 1)

        comment2 = MagicMock()
        comment2.id = 222
        comment2.body = "Second comment"
        comment2.user.login = "user2"
        comment2.created_at = datetime(2023, 1, 2)
        comment2.updated_at = datetime(2023, 1, 2)

        self.pr_mock.get_issue_comments.return_value = [comment1, comment2]

        result = tool.execute({"repo": "owner/repo", "pr_number": 123})

        self.github_mock.get_repo.assert_called_once_with("owner/repo")
        self.repo_mock.get_pull.assert_called_once_with(123)
        self.pr_mock.get_issue_comments.assert_called_once()

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["id"], 111)
        self.assertEqual(result[0]["body"], "First comment")
        self.assertEqual(result[0]["user"], "user1")
        self.assertEqual(result[1]["id"], 222)
        self.assertEqual(result[1]["body"], "Second comment")
        self.assertEqual(result[1]["user"], "user2")

    def test_update_or_create_pr_comment_tool_create_new(self):
        tool = UpdateOrCreatePullRequestCommentTool(self.github_mock)

        # Set up an empty list of comments
        self.pr_mock.get_issue_comments.return_value = []

        # Configure the comment mock
        self.comment_mock.id = 789
        self.comment_mock.html_url = (
            "https://github.com/owner/repo/pull/123#issuecomment-789"
        )

        result = tool.execute(
            {
                "repo": "owner/repo",
                "pr_number": 123,
                "body": "## AI Code Review\n\nThis is a new comment",
                "header_marker": "## AI Code Review\n\n",
            }
        )

        self.github_mock.get_repo.assert_called_once_with("owner/repo")
        self.repo_mock.get_pull.assert_called_once_with(123)
        self.pr_mock.get_issue_comments.assert_called_once()
        self.pr_mock.create_issue_comment.assert_called_once_with(
            "## AI Code Review\n\nThis is a new comment"
        )

        self.assertEqual(result["id"], 789)
        self.assertEqual(
            result["url"], "https://github.com/owner/repo/pull/123#issuecomment-789"
        )
        self.assertEqual(result["action"], "created")

    def test_update_or_create_pr_comment_tool_update_existing(self):
        tool = UpdateOrCreatePullRequestCommentTool(self.github_mock)

        # Create a mock for existing comment
        existing_comment = MagicMock()
        existing_comment.id = 333
        existing_comment.body = "## AI Code Review\n\nOld review content"
        existing_comment.html_url = (
            "https://github.com/owner/repo/pull/123#issuecomment-333"
        )

        # Add user mock to match the login condition in the tool
        existing_comment.user = MagicMock()
        existing_comment.user.login = self.github_mock.get_user.return_value.login

        # Set up list with the existing comment
        self.pr_mock.get_issue_comments.return_value = [existing_comment]

        result = tool.execute(
            {
                "repo": "owner/repo",
                "pr_number": 123,
                "body": "## AI Code Review\n\nUpdated review content",
                "header_marker": "## AI Code Review\n\n",
            }
        )

        self.github_mock.get_repo.assert_called_once_with("owner/repo")
        self.repo_mock.get_pull.assert_called_once_with(123)
        self.pr_mock.get_issue_comments.assert_called_once()
        existing_comment.edit.assert_called_once_with(
            "## AI Code Review\n\nUpdated review content"
        )
        self.pr_mock.create_issue_comment.assert_not_called()

        self.assertEqual(result["id"], 333)
        self.assertEqual(
            result["url"], "https://github.com/owner/repo/pull/123#issuecomment-333"
        )
        self.assertEqual(result["action"], "updated")

    def test_get_issue_tool(self):
        tool = GetIssueTool(self.github_mock)

        result = tool.execute({"repo": "owner/repo", "issue_number": 123})

        self.github_mock.get_repo.assert_called_once_with("owner/repo")
        self.repo_mock.get_issue.assert_called_once_with(123)

        self.assertEqual(result["number"], 123)
        self.assertEqual(result["title"], "Test Issue")
        self.assertEqual(result["body"], "Test issue description")

    def test_add_issue_comment_tool(self):
        tool = AddIssueCommentTool(self.github_mock)

        result = tool.execute(
            {
                "repo": "owner/repo",
                "issue_number": 123,
                "body": "This is a test comment",
            }
        )

        self.github_mock.get_repo.assert_called_once_with("owner/repo")
        self.repo_mock.get_issue.assert_called_once_with(123)
        self.issue_mock.create_comment.assert_called_once_with("This is a test comment")

        self.assertEqual(result["id"], 456)
        self.assertEqual(
            result["url"], "https://github.com/owner/repo/pull/123#issuecomment-456"
        )

    def test_get_repository_tool(self):
        tool = GetRepositoryTool(self.github_mock)
        self.repo_mock.name = "repo"
        self.repo_mock.full_name = "owner/repo"
        self.repo_mock.description = "Test repo"
        self.repo_mock.language = "Python"
        self.repo_mock.topics = ["ai", "github-action"]
        self.repo_mock.forks_count = 5
        self.repo_mock.stargazers_count = 10
        self.repo_mock.open_issues_count = 2
        self.repo_mock.created_at = None
        self.repo_mock.updated_at = None
        self.repo_mock.default_branch = "main"
        self.repo_mock.license = None

        result = tool.execute({"repo": "owner/repo"})

        self.github_mock.get_repo.assert_called_once_with("owner/repo")

        self.assertEqual(result["name"], "repo")
        self.assertEqual(result["full_name"], "owner/repo")
        self.assertEqual(result["description"], "Test repo")
        self.assertEqual(result["language"], "Python")
        self.assertEqual(result["topics"], ["ai", "github-action"])


if __name__ == "__main__":
    unittest.main()
