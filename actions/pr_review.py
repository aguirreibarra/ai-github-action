import fnmatch
import os
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("pr-review-action")


class PRReviewAction:
    """Action for reviewing pull requests."""

    def __init__(self, agent, event):
        """Initialize the PR review action.

        Args:
            agent: The GitHub agent
            event: The GitHub event data
        """
        self.agent = agent
        self.event = event
        self.max_files = int(os.environ.get("MAX_FILES", 10))
        self.include_patterns = self._parse_patterns(
            os.environ.get("INCLUDE_PATTERNS", "")
        )
        self.exclude_patterns = self._parse_patterns(
            os.environ.get("EXCLUDE_PATTERNS", "")
        )

    def _parse_patterns(self, patterns_str: str) -> List[str]:
        """Parse comma-separated glob patterns."""
        if not patterns_str:
            return []
        return [p.strip() for p in patterns_str.split(",")]

    def _match_files(self, files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter files based on include/exclude patterns."""
        if not self.include_patterns and not self.exclude_patterns:
            return files[: self.max_files]

        matched_files = []

        for file in files:
            filename = file.get("filename", "")
            # Check if file should be excluded
            if self.exclude_patterns and any(
                fnmatch.fnmatch(filename, pattern) for pattern in self.exclude_patterns
            ):
                continue

            # Check if file should be included
            if not self.include_patterns or any(
                fnmatch.fnmatch(filename, pattern) for pattern in self.include_patterns
            ):
                matched_files.append(file)

                # Respect max files limit
                if len(matched_files) >= self.max_files:
                    break

        return matched_files

    def run(self) -> Dict[str, Any]:
        """Run the PR review action."""
        try:
            # Extract PR information from event
            pr_number = self.event.get("pull_request", {}).get("number")
            repo_name = self.event.get("repository", {}).get("full_name")

            if not pr_number or not repo_name:
                logger.error("Missing required PR information in GitHub event")
                return {
                    "summary": "Error: Could not extract PR information from GitHub event",
                    "details": "Make sure this action is triggered on pull request events",
                    "suggestions": "",
                }

            # Get PR information using agent
            pr_info = self.agent.execute_tool(
                "get_pull_request", {"repo": repo_name, "pr_number": pr_number}
            )

            # Get PR files
            pr_files = self.agent.execute_tool(
                "get_pull_request_files", {"repo": repo_name, "pr_number": pr_number}
            )

            # Filter files based on patterns
            filtered_files = self._match_files(pr_files)

            # Get PR diff for filtered files
            pr_diff = ""
            for file in filtered_files:
                file_diff = self.agent.execute_tool(
                    "get_pull_request_diff",
                    {
                        "repo": repo_name,
                        "pr_number": pr_number,
                        "filename": file["filename"],
                    },
                )
                pr_diff += f"File: {file['filename']}\n{file_diff}\n\n"

            # Construct message for the agent
            message = (
                f"Please review this pull request:\n\n"
                f"Title: {pr_info.get('title', 'No title')}\n"
                f"Description: {pr_info.get('body', 'No description')}\n\n"
                f"The PR includes changes to {len(filtered_files)} files. "
                f"Here are the diffs:\n\n{pr_diff}\n\n"
                f"Please analyze the code and provide:\n"
                f"1. A summary of the changes\n"
                f"2. Code quality assessment\n"
                f"3. Potential issues or bugs\n"
                f"4. Suggestions for improvement\n"
                f"5. Overall assessment (approve, request changes, comment)"
            )

            # Process message with agent
            context = f"Pull request review for {repo_name}#{pr_number}"
            response = self.agent.process_message(message, context)

            # Post comment to PR
            self.agent.execute_tool(
                "add_pull_request_comment",
                {
                    "repo": repo_name,
                    "pr_number": pr_number,
                    "body": f"## AI Code Review\n\n{response['content']}",
                },
            )

            # Extract structured data from the response
            lines = response["content"].split("\n")
            summary = ""
            details = ""
            suggestions = ""

            current_section = None
            for line in lines:
                if "summary" in line.lower() or "changes" in line.lower():
                    current_section = "summary"
                    continue
                elif (
                    "issue" in line.lower()
                    or "bug" in line.lower()
                    or "problem" in line.lower()
                ):
                    current_section = "details"
                    continue
                elif (
                    "suggest" in line.lower()
                    or "improvement" in line.lower()
                    or "recommend" in line.lower()
                ):
                    current_section = "suggestions"
                    continue

                if current_section == "summary":
                    summary += line + "\n"
                elif current_section == "details":
                    details += line + "\n"
                elif current_section == "suggestions":
                    suggestions += line + "\n"

            # Return results
            return {
                "summary": summary.strip(),
                "details": details.strip(),
                "suggestions": suggestions.strip(),
            }

        except Exception as e:
            logger.error(f"Error running PR review action: {str(e)}")
            return {"summary": f"Error: {str(e)}", "details": "", "suggestions": ""}
