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
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("ai-github-action")

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
        model=os.environ.get("MODEL", "gpt-4-turbo"),
        custom_prompt=os.environ.get("CUSTOM_PROMPT"),
    )
    
    # Run appropriate action based on action_type
    try:
        if action_type == "pr-review":
            action = PRReviewAction(agent, event)
            results = action.run()
        elif action_type == "issue-analyze":
            action = IssueAnalyzeAction(agent, event)
            results = action.run()
        elif action_type == "code-scan":
            action = CodeScanAction(agent, event)
            results = action.run()
        else:
            logger.error(f"Unknown action type: {action_type}")
            sys.exit(1)
        
        # Set outputs
        if results:
            with open(os.environ.get("GITHUB_OUTPUT", "/dev/null"), "a") as f:
                # Use GitHub's multiline output format with delimiters
                # https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions#multiline-strings
                
                # Write summary
                summary = results.get('summary', '')
                if summary:
                    f.write("summary<<EOF\n")
                    f.write(f"{summary}\n")
                    f.write("EOF\n")
                else:
                    f.write("summary=\n")
                
                # Write details
                details = results.get('details', '')
                if details:
                    f.write("details<<EOF\n")
                    f.write(f"{details}\n")
                    f.write("EOF\n")
                else:
                    f.write("details=\n")
                
                # Write suggestions
                suggestions = results.get('suggestions', '')
                if suggestions:
                    f.write("suggestions<<EOF\n")
                    f.write(f"{suggestions}\n")
                    f.write("EOF\n")
                else:
                    f.write("suggestions=\n")
        
        logger.info("Action completed successfully")
    
    except Exception as e:
        logger.error(f"Error running action: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()