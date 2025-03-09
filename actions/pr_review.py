import fnmatch
import os
import logging
from typing import Any

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

    def _parse_patterns(self, patterns_str: str) -> list[str]:
        """Parse comma-separated glob patterns."""
        if not patterns_str:
            return []
        return [p.strip() for p in patterns_str.split(",")]

    def _match_files(self, files: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Filter files based on include/exclude patterns."""
        if not self.include_patterns and not self.exclude_patterns:
            return files[: self.max_files]

        # First pass: filter based on patterns
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

        # Always sort files by number of changes (more changes = higher priority)
        # This ensures consistent ordering for testing and user experience
        matched_files.sort(key=lambda f: f.get("changes", 0), reverse=True)

        # Then limit to max_files if needed
        if len(matched_files) > self.max_files:
            matched_files = matched_files[: self.max_files]

        return matched_files

    def run(self) -> dict[str, Any]:
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

            # Get PR diff for filtered files using a more efficient approach
            pr_diff = ""

            # First, get all the filenames
            filenames = [file["filename"] for file in filtered_files]
            logger.info(
                f"Getting diffs for {len(filenames)} files: {', '.join(filenames[:3])}{'...' if len(filenames) > 3 else ''}"
            )

            # Process files one by one but could be parallelized in the future
            for file in filtered_files:
                try:
                    file_diff = self.agent.execute_tool(
                        "get_pull_request_diff",
                        {
                            "repo": repo_name,
                            "pr_number": pr_number,
                            "filename": file["filename"],
                        },
                    )
                    file_status = file.get("status", "modified")
                    additions = file.get("additions", 0)
                    deletions = file.get("deletions", 0)
                    pr_diff += f"File: {file['filename']} ({file_status}, +{additions}/-{deletions})\n{file_diff}\n\n"
                except Exception as e:
                    logger.error(
                        f"Error getting diff for file {file['filename']}: {str(e)}"
                    )
                    pr_diff += (
                        f"File: {file['filename']} (Error: Could not retrieve diff)\n\n"
                    )

            # Construct message for the agent
            auto_approve = os.environ.get("AUTO_APPROVE", "false").lower() == "true"
            approval_instruction = ""
            
            if auto_approve:
                approval_instruction = (
                    f"\n\n6. If you believe the PR should be approved, explicitly call the approve_pull_request tool with: "
                    f"repo=\"{repo_name}\", pr_number={pr_number}, and an appropriate approval message. "
                    f"Only call this tool if you're confident the PR meets quality standards and is ready to merge."
                )

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
                f"{approval_instruction}"
            )

            # Process message with agent
            context = f"Pull request review for {repo_name}#{pr_number}"
            response = self.agent.process_message(message, context)

            # Unique header for AI review comments - used to identify our comments when updating
            comment_header = "## AI Code Review\n\n"

            # Post or update comment on PR
            result = self.agent.execute_tool(
                "update_or_create_pr_comment",
                {
                    "repo": repo_name,
                    "pr_number": pr_number,
                    "body": f"{comment_header}{response['content']}",
                    "header_marker": comment_header,
                },
            )

            logger.info(f"PR comment {result['action']} with ID {result['id']}")

            # Extract structured data from the response using a more robust approach
            lines = response["content"].split("\n")
            sections: dict[str, list[str]] = {
                "summary": [],
                "details": [],
                "suggestions": [],
                "assessment": [],
            }

            # Define section markers with variations
            section_markers = {
                "summary": ["summary", "changes", "overview", "what changed"],
                "details": [
                    "issue",
                    "bug",
                    "problem",
                    "concern",
                    "potential issues",
                    "code quality",
                ],
                "suggestions": [
                    "suggest",
                    "improvement",
                    "recommend",
                    "enhancement",
                    "optimization",
                ],
                "assessment": [
                    "overall",
                    "assessment",
                    "conclusion",
                    "verdict",
                    "approve",
                ],
            }

            # First pass: identify section headers and their line numbers
            section_boundaries = []
            for i, line in enumerate(lines):
                line_lower = line.lower()

                # Check if line contains any section marker
                for section, markers in section_markers.items():
                    if any(marker in line_lower for marker in markers):
                        # Check if it's a header (often has special chars like #, *, etc.)
                        if (
                            line_lower.startswith("#")
                            or line_lower.startswith("*")
                            or line_lower.startswith("-")
                            or any(f"{num}." in line_lower[:4] for num in range(1, 6))
                        ):
                            section_boundaries.append((i, section))
                            break

            # Sort by line number
            section_boundaries.sort()

            # Second pass: extract content between section boundaries
            for i, (line_num, section) in enumerate(section_boundaries):
                start = line_num + 1  # Skip the header line

                # If there's a next section, end at that section
                if i < len(section_boundaries) - 1:
                    end = section_boundaries[i + 1][0]
                else:
                    end = len(lines)

                # Add lines to the appropriate section
                sections[section].extend(lines[start:end])

            # If no sections were found, try to intelligently assign content
            if all(len(content) == 0 for content in sections.values()):
                for line in lines:
                    line_lower = line.lower()
                    # Try to infer which section this belongs to
                    for section, markers in section_markers.items():
                        if any(marker in line_lower for marker in markers):
                            sections[section].append(line)
                            break

            # Join the lines for each section
            summary = "\n".join(sections["summary"])
            details = "\n".join(sections["details"])
            suggestions = "\n".join(sections["suggestions"])
            assessment = "\n".join(sections["assessment"])

            # With the tool-based approach, we don't need to parse the assessment
            # The AI will call the approve_pull_request tool directly if it decides to approve
            should_approve = False
            
            # We still set this flag to indicate if approval was possible in this run
            auto_approve = os.environ.get("AUTO_APPROVE", "false").lower() == "true"
            
            # Check response for any tool calls made by the AI
            tool_calls = response.get("tool_calls", [])
            
            for tool_call in tool_calls:
                if tool_call.get("name") == "approve_pull_request":
                    # The AI decided to approve by explicitly calling the tool
                    should_approve = True
                    logger.info("AI explicitly called the approve tool - PR was approved")

            # Return results
            return {
                "summary": summary.strip(),
                "details": details.strip(),
                "suggestions": suggestions.strip(),
                "assessment": assessment.strip(),
                "approved": should_approve,
            }

        except Exception as e:
            logger.error(f"Error running PR review action: {str(e)}")
            raise
