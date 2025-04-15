import asyncio
import json
import logging
import sys

from agents import gen_trace_id, trace

from src.actions.code_scan import CodeScanAction
from src.actions.issue_analyze import IssueAnalyzeAction
from src.actions.pr_review import PRReviewAction
from src.constants import (
    ACTION_TYPE,
    GITHUB_EVENT_PATH,
    GITHUB_TOKEN,
    LOG_LEVEL,
    OPENAI_API_KEY,
)

# Configure logging
log_level = getattr(logging, LOG_LEVEL, logging.INFO)

# Configure root logger - this affects all loggers in the application
logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Get our main logger
logger = logging.getLogger("ai-github-action")
logger.info(f"Logging initialized with level: {logging.getLevelName(log_level)}")


def get_github_event():
    """Read GitHub event data from the event file."""
    if not GITHUB_EVENT_PATH:
        logger.error("GITHUB_EVENT_PATH environment variable not set")
        sys.exit(1)

    with open(GITHUB_EVENT_PATH, "r") as f:
        return json.load(f)


async def async_main():
    """Asynchronous main entry point for the GitHub Action."""
    event = get_github_event()

    if not ACTION_TYPE:
        logger.fatal("ACTION_TYPE input not provided")
        sys.exit(1)

    if not GITHUB_TOKEN:
        logger.fatal("GITHUB_TOKEN input not provided")
        sys.exit(1)

    if not OPENAI_API_KEY:
        logger.fatal("OPENAI_API_KEY input not provided")
        sys.exit(1)

    # Generate a trace ID for the entire action
    trace_id = gen_trace_id()
    logger.info(f"Action trace ID: {trace_id}")
    logger.info(f"View trace: https://platform.openai.com/traces/{trace_id}")

    # Run appropriate action based on action_type with tracing
    with trace("GitHub Action", trace_id=trace_id):
        try:
            if ACTION_TYPE == "pr-review":
                action = PRReviewAction(event)
                await action.run()
            elif ACTION_TYPE == "issue-analyze":
                action = IssueAnalyzeAction(event)
                await action.run()
            elif ACTION_TYPE == "code-scan":
                action = CodeScanAction(event)
                await action.run()
            else:
                logger.error(f"Unknown action type: {ACTION_TYPE}")
                sys.exit(1)

            logger.info("Action completed successfully")

        except Exception as e:
            logger.error(f"Error running action: {str(e)}", exc_info=True)
            sys.exit(1)


def main():
    """Main entry point for the GitHub Action."""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
