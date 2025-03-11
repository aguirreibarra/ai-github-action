import os
import unittest
from unittest.mock import MagicMock, patch
from actions.pr_review import PRReviewAction


class TestPRReviewAction(unittest.TestCase):
    """Tests for the PR Review Action class."""

    def setUp(self):
        """Set up tests with mock agent and event."""
        self.agent = MagicMock()
        self.event = {
            "pull_request": {"number": 123},
            "repository": {"full_name": "owner/repo"},
        }
        # Set up environment variables for testing
        os.environ["MAX_FILES"] = "5"
        os.environ["INCLUDE_PATTERNS"] = "*.py,*.js"
        os.environ["EXCLUDE_PATTERNS"] = "*.md,test_*"

    def test_init(self):
        """Test initialization of the PR review action."""
        action = PRReviewAction(self.agent, self.event)

        # Check initialization
        self.assertEqual(action.agent, self.agent)
        self.assertEqual(action.event, self.event)
        self.assertEqual(action.max_files, 5)
        self.assertEqual(action.include_patterns, ["*.py", "*.js"])
        self.assertEqual(action.exclude_patterns, ["*.md", "test_*"])

    def test_parse_patterns(self):
        """Test pattern parsing."""
        action = PRReviewAction(self.agent, self.event)

        # Test with comma-separated patterns
        patterns = action._parse_patterns("*.py,*.js, *.jsx")
        self.assertEqual(patterns, ["*.py", "*.js", "*.jsx"])

        # Test with empty string
        patterns = action._parse_patterns("")
        self.assertEqual(patterns, [])

    def test_match_files(self):
        """Test file matching based on patterns."""
        action = PRReviewAction(self.agent, self.event)

        # Test files
        files = [
            {"filename": "main.py", "changes": 10},
            {"filename": "README.md", "changes": 5},
            {"filename": "test_utils.py", "changes": 8},
            {"filename": "script.js", "changes": 15},
            {"filename": "styles.css", "changes": 20},
            {"filename": "utils.py", "changes": 3},
        ]

        # Match files
        matched = action._match_files(files)

        # Should match main.py, script.js, and utils.py (not README.md or test_utils.py)
        # And max_files is 5, so all 3 matching files should be included
        self.assertEqual(len(matched), 3)

        # Get filenames to check inclusion/exclusion
        filenames = [f["filename"] for f in matched]

        # Verify correct files are included
        self.assertIn("main.py", filenames)
        self.assertIn("script.js", filenames)
        self.assertIn("utils.py", filenames)

        # Verify that exclusion patterns are working (README.md and test_utils.py excluded)
        self.assertNotIn("README.md", filenames)
        self.assertNotIn("test_utils.py", filenames)

        # Verify that non-matching files are excluded (styles.css)
        self.assertNotIn("styles.css", filenames)

        # Now verify the order (files should be sorted by changes)
        # We can't run this test directly since the order is determined by
        # a sort operation, which might be unstable for equal values
        # Instead, let's check that the file with the most changes comes first
        # and the one with the least changes comes last
        self.assertEqual(matched[0]["filename"], "script.js")  # Most changes (15)
        self.assertEqual(matched[-1]["filename"], "utils.py")  # Least changes (3)

    @patch.dict(os.environ, {"MAX_FILES": "2"})
    def test_match_files_respects_max_files(self):
        """Test that file matching respects the max_files limit."""
        action = PRReviewAction(self.agent, self.event)

        # Test files
        files = [
            {"filename": "main.py", "changes": 10},
            {"filename": "script.js", "changes": 15},
            {"filename": "utils.py", "changes": 3},
        ]

        # Match files
        matched = action._match_files(files)

        # Should only include top 2 files by changes
        self.assertEqual(len(matched), 2)
        self.assertEqual(matched[0]["filename"], "script.js")  # Highest changes first
        self.assertEqual(matched[1]["filename"], "main.py")

    @patch.dict(os.environ, {"INCLUDE_PATTERNS": "", "EXCLUDE_PATTERNS": ""})
    def test_match_files_no_patterns(self):
        """Test file matching with no patterns."""
        action = PRReviewAction(self.agent, self.event)

        # Test files
        files = [
            {"filename": "main.py", "changes": 10},
            {"filename": "README.md", "changes": 5},
            {"filename": "script.js", "changes": 15},
        ]

        # Match files
        matched = action._match_files(files)

        # Should include all files up to max_files (5)
        self.assertEqual(len(matched), 3)

    def test_run_success(self):
        """Test successful PR review run."""
        # Mock agent responses
        self.agent.execute_tool.side_effect = [
            # get_pull_request
            {"title": "Test PR", "body": "This is a test PR"},
            # get_pull_request_files
            [
                {
                    "filename": "main.py",
                    "status": "modified",
                    "additions": 10,
                    "deletions": 5,
                },
                {
                    "filename": "utils.js",
                    "status": "added",
                    "additions": 20,
                    "deletions": 0,
                },
            ],
            # get_pull_request_diff for main.py
            "+ print('Added line')\n- print('Removed line')",
            # get_pull_request_diff for utils.js
            "+ function test() { return true; }",
            # update_or_create_pr_comment
            {"id": 456, "action": "created"},
        ]

        # Mock process_message response
        self.agent.process_message.return_value = {
            "content": (
                "# Summary\nThis PR adds a test function to utils.js and modifies main.py.\n\n"
                "# Code Quality\nCode looks good.\n\n"
                "# Suggestions\nConsider adding tests.\n\n"
                "# Overall Assessment\nApprove this PR."
            )
        }

        action = PRReviewAction(self.agent, self.event)
        # run() returns None, so we just call it to make sure it doesn't raise exceptions
        action.run()

        # Check that agent was called correctly
        self.assertEqual(self.agent.execute_tool.call_count, 5)
        self.assertEqual(self.agent.process_message.call_count, 1)

    def test_run_missing_pr_info(self):
        """Test handling of missing PR information."""
        # Event with missing PR number
        event_missing_pr = {"repository": {"full_name": "owner/repo"}}

        action = PRReviewAction(self.agent, event_missing_pr)

        # Should raise a ValueError
        with self.assertRaises(ValueError):
            action.run()

        # No agent calls should be made
        self.agent.execute_tool.assert_not_called()


if __name__ == "__main__":
    unittest.main()
