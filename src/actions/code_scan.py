"""
Action for scanning code repositories using OpenAI Agents SDK.
"""

import logging
from typing import Any

from agents import Runner, custom_span
from github import Github

from src.constants import CUSTOM_PROMPT, GITHUB_TOKEN, MAX_TURNS, MODEL
from src.context.github_context import GithubContext
from src.github_agents.code_scan_agent import create_code_scan_agent

logger = logging.getLogger("code-scan-action")


class CodeScanAction:
    """Action for scanning code repositories."""

    def __init__(self, event: dict[str, Any]):
        """Initialize the code scan action.

        Args:
            agent: The GitHub agent
            event: The GitHub event data
        """
        logger.info("Initializing Code Scan Action")
        self.agent = create_code_scan_agent(model=MODEL, custom_prompt=CUSTOM_PROMPT)
        self.event = event

    async def run(self) -> None:
        """Run the code scan action asynchronously."""
        logger.info("Starting code scan action")

        with custom_span("Code Scan Action"):
            try:
                repo_name = self.event.get("repository", {}).get("full_name")

                logger.info(f"Processing repository: {repo_name}")

                if not repo_name:
                    logger.error(
                        "Missing required repository information in GitHub event"
                    )
                    raise ValueError(
                        "Missing required repository information in GitHub event"
                    )

                message = f"Please scan the repository: {repo_name}\n"

                with custom_span("Run code scan"):
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
                    logger.info(f"Code scan response: {final_output}")

            except Exception as e:
                logger.critical(
                    f"Unhandled exception in code scan action: {str(e)}", exc_info=True
                )
                raise
