#!/usr/bin/env python3

import os
import sys
import json
import logging
from github_agent import GitHubAgent
from actions.pr_review import PRReviewAction
from actions.issue_analyze import IssueAnalyzeAction
from actions.code_scan import CodeScanAction

# Configure logging
# Get log level from environment variable, default to INFO
log_level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, log_level_name, logging.INFO)

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
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        logger.error("GITHUB_EVENT_PATH environment variable not set")
        sys.exit(1)

    with open(event_path, "r") as f:
        return json.load(f)


def main():
    """Main entry point for the GitHub Action."""
    # Get GitHub event data
    event = get_github_event()

    # Get action type from inputs
    action_type = os.environ.get("ACTION_TYPE")
    if not action_type:
        logger.error("ACTION_TYPE input not provided")
        sys.exit(1)

    # Get GitHub token and OpenAI API key
    github_token = os.environ.get("GITHUB_TOKEN")
    openai_api_key = os.environ.get("OPENAI_API_KEY")

    if not github_token:
        logger.error("GITHUB_TOKEN input not provided")
        sys.exit(1)

    if not openai_api_key:
        logger.error("OPENAI_API_KEY input not provided")
        sys.exit(1)

    # Initialize GitHub agent
    agent = GitHubAgent(
        github_token=github_token,
        openai_api_key=openai_api_key,
        model=os.environ.get("MODEL", "gpt-4o-mini"),
        custom_prompt=os.environ.get("CUSTOM_PROMPT"),
        action_type=action_type,
    )

    # Run appropriate action based on action_type
    try:
        if action_type == "pr-review":
            action = PRReviewAction(agent, event)
            action.run()
        elif action_type == "issue-analyze":
            action = IssueAnalyzeAction(agent, event)
            action.run()
        elif action_type == "code-scan":
            action = CodeScanAction(agent, event)
            action.run()
        else:
            logger.error(f"Unknown action type: {action_type}")
            sys.exit(1)

        logger.info("Action completed successfully")

    except Exception as e:
        logger.error(f"Error running action: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
