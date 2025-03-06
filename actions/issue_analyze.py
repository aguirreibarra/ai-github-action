import logging
from typing import Dict, Any

logger = logging.getLogger("issue-analyze-action")


class IssueAnalyzeAction:
    """Action for analyzing GitHub issues."""

    def __init__(self, agent, event):
        """Initialize the issue analysis action.

        Args:
            agent: The GitHub agent
            event: The GitHub event data
        """
        self.agent = agent
        self.event = event

    def run(self) -> Dict[str, Any]:
        """Run the issue analysis action."""
        try:
            # Extract issue information from event
            issue_number = self.event.get("issue", {}).get("number")
            repo_name = self.event.get("repository", {}).get("full_name")

            if not issue_number or not repo_name:
                logger.error("Missing required issue information in GitHub event")
                return {
                    "summary": "Error: Could not extract issue information from GitHub event",
                    "details": "Make sure this action is triggered on issue events",
                    "suggestions": "",
                }

            # Get issue information using agent
            issue_info = self.agent.execute_tool(
                "get_issue", {"repo": repo_name, "issue_number": issue_number}
            )

            # Get repository information
            repo_info = self.agent.execute_tool("get_repository", {"repo": repo_name})

            # Construct message for the agent
            message = (
                f"Please analyze this GitHub issue:\n\n"
                f"Repository: {repo_name}\n"
                f"Issue #{issue_number}: {issue_info.get('title', 'No title')}\n"
                f"Description: {issue_info.get('body', 'No description')}\n\n"
                f"Labels: {', '.join(label['name'] for label in issue_info.get('labels', []))}\n\n"
                f"Repository description: {repo_info.get('description', 'No description')}\n\n"
                f"Please provide:\n"
                f"1. A summary of the issue\n"
                f"2. Analysis of what the issue is about\n"
                f"3. Suggested next steps or how to address it\n"
                f"4. Recommend labels if appropriate\n"
                f"5. Whether this should be classified as a bug, feature request, or question"
            )

            # Process message with agent
            context = f"Issue analysis for {repo_name}#{issue_number}"
            response = self.agent.process_message(message, context)

            # Post comment to issue
            self.agent.execute_tool(
                "add_issue_comment",
                {
                    "repo": repo_name,
                    "issue_number": issue_number,
                    "body": f"## AI Issue Analysis\n\n{response['content']}",
                },
            )

            # Extract structured data from the response
            lines = response["content"].split("\n")
            summary = ""
            details = ""
            suggestions = ""

            current_section = None
            for line in lines:
                if "summary" in line.lower():
                    current_section = "summary"
                    continue
                elif "analysis" in line.lower():
                    current_section = "details"
                    continue
                elif (
                    "suggest" in line.lower()
                    or "next step" in line.lower()
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
            logger.error(f"Error running issue analysis action: {str(e)}")
            return {"summary": f"Error: {str(e)}", "details": "", "suggestions": ""}
