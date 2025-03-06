import unittest
from unittest.mock import MagicMock
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.github_tools import (
    GetPullRequestTool,
    GetPullRequestFilesTool,
    GetPullRequestDiffTool,
    AddPullRequestCommentTool,
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
