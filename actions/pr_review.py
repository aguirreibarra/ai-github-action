import fnmatch
import os
import logging
from typing import Any

# Configure logger
logger = logging.getLogger("pr-review-action")


class PRReviewAction:
    """Action for reviewing pull requests.

    Logging Strategy:
    - DEBUG: Implementation details useful for troubleshooting
    - INFO: High-level workflow progress and main operations
    - WARNING: Potential issues that don't prevent operation
    - ERROR: Issues that prevent normal operation
    - CRITICAL: Severe failures

    Set LOG_LEVEL environment variable to control verbosity:
    - Production environments: INFO or WARNING
    - Development/testing: DEBUG
    """

    def __init__(self, agent, event):
        """Initialize the PR review action.

        Args:
            agent: The GitHub agent
            event: The GitHub event data
        """
        logger.info("Initializing PR Review Action")
        self.agent = agent
        self.event = event
        self.max_files = int(os.environ.get("MAX_FILES", 10))
        self.include_patterns = self._parse_patterns(
            os.environ.get("INCLUDE_PATTERNS", "")
        )
        self.exclude_patterns = self._parse_patterns(
            os.environ.get("EXCLUDE_PATTERNS", "")
        )
        logger.debug(
            f"Max files: {self.max_files}, Include patterns: {self.include_patterns}, Exclude patterns: {self.exclude_patterns}"
        )

    def _parse_patterns(self, patterns_str: str) -> list[str]:
        """Parse comma-separated glob patterns."""
        logger.debug(f"Parsing patterns: '{patterns_str}'")
        if not patterns_str:
            return []
        return [p.strip() for p in patterns_str.split(",")]

    def _match_files(self, files: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Filter files based on include/exclude patterns."""
        logger.info(f"Matching files. Total files to process: {len(files)}")
        if not self.include_patterns and not self.exclude_patterns:
            logger.debug(
                f"No patterns specified, returning first {self.max_files} files"
            )
            return files[: self.max_files]

        # First pass: filter based on patterns
        matched_files = []

        for file in files:
            filename = file.get("filename", "")
            # Check if file should be excluded
            if self.exclude_patterns and any(
                fnmatch.fnmatch(filename, pattern) for pattern in self.exclude_patterns
            ):
                logger.debug(f"Excluding file {filename} based on exclude patterns")
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
            logger.warning(
                f"Limiting matched files from {len(matched_files)} to {self.max_files}"
            )
            matched_files = matched_files[: self.max_files]
        else:
            logger.debug(f"Found {len(matched_files)} matched files")

        return matched_files

    def run(self) -> dict[str, Any]:
        """Run the PR review action."""
        logger.info("Starting PR review action")
        try:
            # Extract PR information from event
            pr_number = self.event.get("pull_request", {}).get("number")
            repo_name = self.event.get("repository", {}).get("full_name")

            logger.info(f"Processing PR #{pr_number} in repository {repo_name}")

            if not pr_number or not repo_name:
                logger.error("Missing required PR information in GitHub event")
                return {
                    "summary": "Error: Could not extract PR information from GitHub event",
                    "details": "Make sure this action is triggered on pull request events",
                    "suggestions": "",
                }

            # Get PR information using agent
            logger.debug(f"Fetching PR information for {repo_name}#{pr_number}")
            pr_info = self.agent.execute_tool(
                "get_pull_request", {"repo": repo_name, "pr_number": pr_number}
            )

            # Get PR files
            logger.debug("Fetching PR files")
            pr_files = self.agent.execute_tool(
                "get_pull_request_files", {"repo": repo_name, "pr_number": pr_number}
            )

            # Filter files based on patterns
            matched_files = self._match_files(pr_files)
            if not matched_files:
                logger.warning("No files matched for review")
                return {
                    "summary": "No files to review",
                    "details": "No files matched the include/exclude patterns or there were no files in the PR",
                    "suggestions": "",
                }

            logger.info(f"Will review {len(matched_files)} files")

            # Get PR diff for filtered files using a more efficient approach
            pr_diff = ""

            # First, get all the filenames
            filenames = [file["filename"] for file in matched_files]
            logger.debug(
                f"Getting diffs for {len(filenames)} files: {', '.join(filenames[:3])}{'...' if len(filenames) > 3 else ''}"
            )

            # Process files one by one but could be parallelized in the future
            for file in matched_files:
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
                    f"\n\n6. IMPORTANT: First provide a complete review with all the sections above. "
                    f"Then, as a SEPARATE STEP AFTER your complete review, if you believe the PR should be approved, "
                    f"explicitly call the approve_pull_request tool with: "
                    f'repo="{repo_name}", pr_number={pr_number}, and a SHORT approval message. '
                    f"Only call this tool if you're confident the PR meets quality standards and is ready to merge."
                )

            message = (
                f"Please review this pull request:\n\n"
                f"Title: {pr_info.get('title', 'No title')}\n"
                f"Description: {pr_info.get('body', 'No description')}\n\n"
                f"The PR includes changes to {len(matched_files)} files. "
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
            logger.debug("Starting first pass: identifying section headers")
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
                            logger.debug(
                                f"Found section '{section}' at line {i}: {line.strip()}"
                            )
                            section_boundaries.append((i, section))
                            break

            # Sort by line number
            section_boundaries.sort()
            logger.info(
                f"Identified {len(section_boundaries)} section boundaries: {[s[1] for s in section_boundaries]}"
            )

            # Second pass: extract content between section boundaries
            logger.debug("Starting second pass: extracting content between sections")
            for i, (line_num, section) in enumerate(section_boundaries):
                start = line_num + 1  # Skip the header line

                # If there's a next section, end at that section
                if i < len(section_boundaries) - 1:
                    end = section_boundaries[i + 1][0]
                else:
                    end = len(lines)

                logger.debug(
                    f"Extracting {section} content from lines {start} to {end}"
                )
                # Add lines to the appropriate section
                sections[section].extend(lines[start:end])

            # If no sections were found, try to intelligently assign content
            if all(len(content) == 0 for content in sections.values()):
                logger.warning(
                    "No structured sections found in AI response, attempting to intelligently assign content"
                )
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

            logger.debug(f"Summary length: {len(summary)} characters")
            logger.debug(f"Details length: {len(details)} characters")
            logger.debug(f"Suggestions length: {len(suggestions)} characters")
            logger.debug(f"Assessment length: {len(assessment)} characters")

            # With the tool-based approach, we don't need to parse the assessment
            # The AI will call the approve_pull_request tool directly if it decides to approve
            should_approve = False

            # We still set this flag to indicate if approval was possible in this run
            auto_approve = os.environ.get("AUTO_APPROVE", "false").lower() == "true"
            logger.info(f"Auto approve setting: {auto_approve}")

            # Check response for any tool calls made by the AI
            tool_calls = response.get("tool_calls", [])
            logger.debug(f"Found {len(tool_calls)} tool calls in AI response")

            for tool_call in tool_calls:
                logger.debug(f"Processing tool call: {tool_call.get('name')}")
                if tool_call.get("name") == "approve_pull_request":
                    # The AI decided to approve by explicitly calling the tool
                    should_approve = True
                    logger.info(
                        "AI explicitly called the approve tool - PR was approved"
                    )

            # Return results
            logger.info(f"Completed PR review. Approved: {should_approve}")
            return {
                "summary": summary.strip(),
                "details": details.strip(),
                "suggestions": suggestions.strip(),
                "assessment": assessment.strip(),
                "approved": should_approve,
            }

        except Exception as e:
            logger.critical(
                f"Unhandled exception in PR review action: {str(e)}", exc_info=True
            )
            return {
                "summary": f"Error reviewing PR: {str(e)}",
                "details": "An unexpected error occurred while reviewing the PR",
                "suggestions": "",
            }
