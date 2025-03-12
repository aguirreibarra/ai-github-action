"""
Action for analyzing GitHub issues using OpenAI Agents SDK.
"""

import logging
from typing import Any

from agents import Runner, custom_span
from github import Github

from src.constants import CUSTOM_PROMPT, GITHUB_TOKEN, MAX_TURNS, MODEL
from src.github_agents.issue_analyze_agent import create_issue_analyze_agent
from src.context.github_context import GithubContext

# Configure logger
logger = logging.getLogger("issue-analyze-action")


class IssueAnalyzeAction:
    """Action for analyzing GitHub issues."""

    def __init__(self, event: dict[str, Any]):
        """Initialize the issue analyze action.

        Args:
            event: The GitHub event data
        """
        logger.info("Initializing Issue Analysis Action")
        self.agent = create_issue_analyze_agent(
            model=MODEL, custom_prompt=CUSTOM_PROMPT
        )
        self.event = event

    async def run(self) -> None:
        """Run the issue analyze action asynchronously."""
        logger.info("Starting issue analysis action")

        with custom_span("Issue Analysis Action"):
            try:
                # Extract issue information from event
                issue_number = self.event.get("issue", {}).get("number")
                repo_name = self.event.get("repository", {}).get("full_name")

                logger.info(
                    f"Processing issue #{issue_number} in repository {repo_name}"
                )

                if not issue_number or not repo_name:
                    logger.error("Missing required issue information in GitHub event")
                    raise ValueError(
                        "Missing required issue information in GitHub event"
                    )

                # Construct message for the agent
                with custom_span("Run issue analysis"):
                    message = (
                        f"Please analyze this GitHub issue:\n\n"
                        f"Repository: {repo_name}\n"
                        f"Issue #{issue_number}: \n"
                        f"Please provide as a comment to the issue:\n"
                        f"1. A summary of the issue\n"
                        f"2. The category (bug, feature request, question, etc.) with confidence level\n"
                        f"3. Estimated complexity (low, medium, high)\n"
                        f"4. Suggested priority (low, medium, high)\n"
                        f"5. Code areas that might be related\n"
                        f"6. Suggested next steps or solutions\n"
                    )

                    context = GithubContext(
                        github_event=self.event,
                        github_client=Github(GITHUB_TOKEN),
                    )
                    result = await Runner.run(
                        starting_agent=self.agent,
                        input=message,
                        context=context,
                        max_turns=MAX_TURNS,
                    )

                    final_output = result.final_output
                    logger.info(f"Final output: {final_output}")

            except Exception as e:
                logger.critical(
                    f"Unhandled exception in issue analysis action: {str(e)}",
                    exc_info=True,
                )
                raise
