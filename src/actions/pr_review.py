import logging
from typing import Any

from agents import Runner, custom_span
from github import Github

from src.constants import (
    CUSTOM_PROMPT,
    GITHUB_TOKEN,
    MAX_TURNS,
    MODEL,
)
from src.github_agents.pr_review_agent import create_pr_review_agent
from src.context.github_context import GithubContext

logger = logging.getLogger("pr-review-action")


class PRReviewAction:
    """Action for reviewing pull requests."""

    def __init__(self, event: dict[str, Any]):
        """Initialize the PR review action.

        Args:
            agent: The GitHub agent
            event: The GitHub event data
        """
        logger.info("Initializing PR Review Action")
        self.agent = create_pr_review_agent(model=MODEL, custom_prompt=CUSTOM_PROMPT)
        self.event = event

    async def run(self) -> None:
        """Run the PR review action asynchronously."""
        logger.info("Starting PR review action")

        with custom_span("PR Review Action"):
            try:
                pr_number = self.event.get("pull_request", {}).get("number")
                repo_name = self.event.get("repository", {}).get("full_name")

                logger.info(f"Processing PR #{pr_number} in repository {repo_name}")

                if not pr_number or not repo_name:
                    logger.error("Missing required PR information in GitHub event")
                    raise ValueError("Missing required PR information in GitHub event")

                with custom_span("Run PR review"):
                    context = GithubContext(
                        github_event=self.event,
                        github_client=Github(GITHUB_TOKEN),
                    )
                    result = await Runner.run(
                        starting_agent=self.agent,
                        input=f"Pull request review for {repo_name}#{pr_number}",
                        context=context,
                        max_turns=MAX_TURNS,
                    )

                    final_output = result.final_output
                    logger.info(f"agent response: {final_output}")

            except Exception as e:
                logger.critical(
                    f"Unhandled exception in PR review action: {str(e)}", exc_info=True
                )
                raise
