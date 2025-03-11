from typing import Any
from abc import ABC, abstractmethod
from github import Github


class GitHubTool(ABC):
    """Base class for GitHub tools."""

    def __init__(self, github_client: Github):
        """Initialize the GitHub tool.

        Args:
            github_client: GitHub client
        """
        self.github = github_client

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description."""
        pass

    @property
    @abstractmethod
    def parameters(self) -> dict[str, Any]:
        """Tool parameters."""
        pass

    @abstractmethod
    def execute(self, parameters: dict[str, Any]) -> Any:
        """Execute the tool."""
        pass

    def to_openai_tool(self) -> dict[str, Any]:
        """Convert the tool to OpenAI tool format."""
        # Extract required parameters
        required_params = [
            k for k, v in self.parameters.items() if v.get("required", False)
        ]

        # Clean up parameter definitions by removing the "required" field
        # since it's not part of the OpenAI schema
        properties = {}
        for param_name, param_def in self.parameters.items():
            # Create a new dict without the "required" key
            clean_param = {k: v for k, v in param_def.items() if k != "required"}
            properties[param_name] = clean_param

        # Prepare the schema following OpenAI API v1+ format
        schema = {
            "type": "object",
            "properties": properties,
        }

        # Only add required field if there are required parameters
        if required_params:
            schema["required"] = required_params

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": schema,
            },
        }


class GetPullRequestTool(GitHubTool):
    """Tool for getting pull request information."""

    @property
    def name(self) -> str:
        return "get_pull_request"

    @property
    def description(self) -> str:
        return "Get information about a pull request"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "repo": {
                "type": "string",
                "description": "Repository name with owner (e.g., 'owner/repo')",
                "required": True,
            },
            "pr_number": {
                "type": "integer",
                "description": "Pull request number",
                "required": True,
            },
        }

    def execute(self, parameters: dict[str, Any]) -> dict[str, Any]:
        repo = self.github.get_repo(parameters["repo"])
        pr = repo.get_pull(parameters["pr_number"])

        return {
            "number": pr.number,
            "title": pr.title,
            "body": pr.body,
            "state": pr.state,
            "user": pr.user.login,
            "created_at": pr.created_at.isoformat() if pr.created_at else None,
            "updated_at": pr.updated_at.isoformat() if pr.updated_at else None,
            "merged": pr.merged,
            "mergeable": pr.mergeable,
            "comments": pr.comments,
            "commits": pr.commits,
            "additions": pr.additions,
            "deletions": pr.deletions,
            "changed_files": pr.changed_files,
        }


class GetPullRequestFilesTool(GitHubTool):
    """Tool for getting files in a pull request."""

    @property
    def name(self) -> str:
        return "get_pull_request_files"

    @property
    def description(self) -> str:
        return "Get the list of files changed in a pull request"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "repo": {
                "type": "string",
                "description": "Repository name with owner (e.g., 'owner/repo')",
                "required": True,
            },
            "pr_number": {
                "type": "integer",
                "description": "Pull request number",
                "required": True,
            },
        }

    def execute(self, parameters: dict[str, Any]) -> list[dict[str, Any]]:
        repo = self.github.get_repo(parameters["repo"])
        pr = repo.get_pull(parameters["pr_number"])

        files = []
        for file in pr.get_files():
            files.append(
                {
                    "filename": file.filename,
                    "status": file.status,
                    "additions": file.additions,
                    "deletions": file.deletions,
                    "changes": file.changes,
                    "blob_url": file.blob_url,
                    "raw_url": file.raw_url,
                    "patch": file.patch if hasattr(file, "patch") else None,
                }
            )

        return files


class GetPullRequestDiffTool(GitHubTool):
    """Tool for getting the diff of a specific file in a pull request."""

    @property
    def name(self) -> str:
        return "get_pull_request_diff"

    @property
    def description(self) -> str:
        return "Get the diff of a specific file in a pull request"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "repo": {
                "type": "string",
                "description": "Repository name with owner (e.g., 'owner/repo')",
                "required": True,
            },
            "pr_number": {
                "type": "integer",
                "description": "Pull request number",
                "required": True,
            },
            "filename": {
                "type": "string",
                "description": "Path to the file",
                "required": True,
            },
        }

    def execute(self, parameters: dict[str, Any]) -> str:
        repo = self.github.get_repo(parameters["repo"])
        pr = repo.get_pull(parameters["pr_number"])
        filename = parameters["filename"]

        for file in pr.get_files():
            if file.filename == filename:
                if hasattr(file, "patch") and file.patch:
                    return file.patch
                else:
                    return f"No diff available for file {filename}"

        return f"File {filename} not found in pull request {parameters['pr_number']}"


class AddPullRequestCommentTool(GitHubTool):
    """Tool for adding a comment to a pull request."""

    @property
    def name(self) -> str:
        return "add_pull_request_comment"

    @property
    def description(self) -> str:
        return "Add a comment to a pull request"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "repo": {
                "type": "string",
                "description": "Repository name with owner (e.g., 'owner/repo')",
                "required": True,
            },
            "pr_number": {
                "type": "integer",
                "description": "Pull request number",
                "required": True,
            },
            "body": {
                "type": "string",
                "description": "Comment content, supports Markdown",
                "required": True,
            },
        }

    def execute(self, parameters: dict[str, Any]) -> dict[str, Any]:
        repo = self.github.get_repo(parameters["repo"])
        pr = repo.get_pull(parameters["pr_number"])
        comment = pr.create_issue_comment(parameters["body"])

        return {
            "id": comment.id,
            "url": comment.html_url,
        }


class ListPullRequestCommentsTool(GitHubTool):
    """Tool for listing comments on a pull request."""

    @property
    def name(self) -> str:
        return "list_pull_request_comments"

    @property
    def description(self) -> str:
        return "List comments on a pull request"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "repo": {
                "type": "string",
                "description": "Repository name with owner (e.g., 'owner/repo')",
                "required": True,
            },
            "pr_number": {
                "type": "integer",
                "description": "Pull request number",
                "required": True,
            },
        }

    def execute(self, parameters: dict[str, Any]) -> list[dict[str, Any]]:
        repo = self.github.get_repo(parameters["repo"])
        pr = repo.get_pull(parameters["pr_number"])
        comments = list(pr.get_issue_comments())

        result = []
        for comment in comments:
            result.append(
                {
                    "id": comment.id,
                    "body": comment.body,
                    "user": comment.user.login,
                    "created_at": comment.created_at.isoformat(),
                    "updated_at": comment.updated_at.isoformat(),
                }
            )

        return result


class CreatePullRequestReviewTool(GitHubTool):
    """Tool for creating a pull request review."""

    @property
    def name(self) -> str:
        return "create_pull_request_review"

    @property
    def description(self) -> str:
        return "Create a review on a pull request with the specified event type ('APPROVE', 'REQUEST_CHANGES', or 'COMMENT')"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "repo": {
                "type": "string",
                "description": "Repository name with owner (e.g., 'owner/repo')",
                "required": True,
            },
            "pr_number": {
                "type": "integer",
                "description": "Pull request number",
                "required": True,
            },
            "event": {
                "type": "string",
                "description": "Review event type: 'APPROVE', 'REQUEST_CHANGES', or 'COMMENT'",
                "required": True,
            },
            "body": {
                "type": "string",
                "description": "Comment to include with the review",
                "required": False,
            },
            "commit_id": {
                "type": "string",
                "description": "The SHA of the commit to review",
                "required": False,
            },
            "comments": {
                "type": "array",
                "description": "List of review comments to add to specific lines",
                "required": False,
                "items": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "The relative path to the file to comment on",
                        },
                        "position": {
                            "type": "integer",
                            "description": "The line index in the diff to comment on",
                        },
                        "body": {
                            "type": "string",
                            "description": "The text of the comment",
                        },
                    },
                },
            },
        }

    def execute(self, parameters: dict[str, Any]) -> dict[str, Any]:
        repo = self.github.get_repo(parameters["repo"])
        pr = repo.get_pull(parameters["pr_number"])

        # Prepare parameters for create_review
        kwargs = {"event": parameters["event"]}

        if "body" in parameters:
            kwargs["body"] = parameters["body"]
        elif parameters["event"] == "APPROVE":
            kwargs["body"] = "Approved after review"

        if "commit_id" in parameters:
            commit = repo.get_commit(parameters["commit_id"])
            kwargs["commit"] = commit

        if "comments" in parameters:
            review_comments = []
            for comment in parameters["comments"]:
                review_comment = {
                    "path": comment["path"],
                    "position": comment["position"],
                    "body": comment["body"],
                }
                review_comments.append(review_comment)
            kwargs["comments"] = review_comments

        review = pr.create_review(**kwargs)

        return {
            "id": review.id,
            "state": review.state,
            "body": review.body,
            "submitted_at": (
                review.submitted_at.isoformat() if review.submitted_at else None
            ),
        }


class CreatePullRequestReviewCommentTool(GitHubTool):
    """Tool for creating a pull request review comment."""

    @property
    def name(self) -> str:
        return "create_pull_request_review_comment"

    @property
    def description(self) -> str:
        return "Create a pull request review comment"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "repo": {
                "type": "string",
                "description": "Repository name with owner (e.g., 'owner/repo')",
                "required": True,
            },
            "pr_number": {
                "type": "integer",
                "description": "Pull request number",
                "required": True,
            },
            "commit_id": {
                "type": "string",
                "description": "The SHA of the commit to review",
                "required": True,
            },
            "body": {
                "type": "string",
                "description": "Comment content, supports Markdown",
                "required": True,
            },
            "path": {
                "type": "string",
                "description": "Path to the file",
                "required": True,
            },
            "line": {
                "type": "integer",
                "description": "Line number to add the comment",
                "required": False,
            },
            "side": {
                "type": "string",
                "description": "Side of the comment (LEFT or RIGHT)",
                "required": False,
            },
            "start_line": {
                "type": "integer",
                "description": "Start line number for multi-line comments",
                "required": False,
            },
            "start_side": {
                "type": "string",
                "description": "Side of the starting line (LEFT or RIGHT)",
                "required": False,
            },
            "in_reply_to": {
                "type": "integer",
                "description": "Comment ID to reply to",
                "required": False,
            },
            "subject_type": {
                "type": "string",
                "description": "Subject type (line or file)",
                "required": False,
            },
            "as_suggestion": {
                "type": "boolean",
                "description": "Whether to add the comment as a suggestion",
                "required": False,
            },
        }

    def execute(self, parameters: dict[str, Any]) -> dict[str, Any]:
        repo = self.github.get_repo(parameters.pop("repo"))
        pr = repo.get_pull(parameters.pop("pr_number"))
        commit_id = parameters.pop("commit_id")
        commit = repo.get_commit(commit_id)

        # We need to validate "path" is a valid file in the PR
        path = parameters.pop("path")
        body = parameters.pop("body")

        # Get the file from the PR to get position info
        found_file = None
        for file in pr.get_files():
            if file.filename == path:
                found_file = file
                break

        if not found_file:
            raise ValueError(f"Path '{path}' not found in the pull request files")

        # Position is required but we might need to calculate it
        # If line is provided but position isn't, we need to determine the position
        if "position" not in parameters and "line" in parameters:
            # We use the position value from file data when possible
            position = parameters.pop("line")
            parameters["position"] = position

        # Create the review comment
        comment = pr.create_review_comment(
            body=body,
            commit=commit,
            path=path,
            **{k: v for k, v in parameters.items() if v is not None},
        )

        return {
            "id": comment.id,
            "url": comment.html_url,
        }


class UpdateOrCreatePullRequestCommentTool(GitHubTool):
    """Tool for updating an existing AI review comment or creating a new one."""

    @property
    def name(self) -> str:
        return "update_or_create_pr_comment"

    @property
    def description(self) -> str:
        return "Update an existing AI review comment or create a new one"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "repo": {
                "type": "string",
                "description": "Repository name with owner (e.g., 'owner/repo')",
                "required": True,
            },
            "pr_number": {
                "type": "integer",
                "description": "Pull request number",
                "required": True,
            },
            "body": {
                "type": "string",
                "description": "Comment content, supports Markdown",
                "required": True,
            },
            "header_marker": {
                "type": "string",
                "description": "Unique identifier at the beginning of comments made by this bot",
                "required": True,
            },
        }

    def execute(self, parameters: dict[str, Any]) -> dict[str, Any]:
        repo = self.github.get_repo(parameters["repo"])
        pr = repo.get_pull(parameters["pr_number"])
        comments = list(pr.get_issue_comments())
        header_marker = parameters["header_marker"]

        # Find existing AI review comment
        existing_comment = None
        for comment in comments:
            if comment.body.startswith(header_marker):
                existing_comment = comment
                break

        # Update existing comment or create new one
        if existing_comment:
            existing_comment.edit(parameters["body"])
            return {
                "id": existing_comment.id,
                "url": existing_comment.html_url,
                "action": "updated",
            }
        else:
            # No existing comment found, create a new one
            new_comment = pr.create_issue_comment(parameters["body"])
            return {
                "id": new_comment.id,
                "url": new_comment.html_url,
                "action": "created",
            }


class GetRepositoryTool(GitHubTool):
    """Tool for getting repository information."""

    @property
    def name(self) -> str:
        return "get_repository"

    @property
    def description(self) -> str:
        return "Get information about a repository"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "repo": {
                "type": "string",
                "description": "Repository name with owner (e.g., 'owner/repo')",
                "required": True,
            },
        }

    def execute(self, parameters: dict[str, Any]) -> dict[str, Any]:
        repo = self.github.get_repo(parameters["repo"])

        return {
            "name": repo.name,
            "full_name": repo.full_name,
            "description": repo.description,
            "language": repo.language,
            "topics": repo.topics,
            "forks": repo.forks_count,
            "stars": repo.stargazers_count,
            "open_issues": repo.open_issues_count,
            "created_at": repo.created_at.isoformat() if repo.created_at else None,
            "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
            "default_branch": repo.default_branch,
            "license": repo.license.name if repo.license else None,
        }


class GetIssueTool(GitHubTool):
    """Tool for getting issue information."""

    @property
    def name(self) -> str:
        return "get_issue"

    @property
    def description(self) -> str:
        return "Get information about an issue"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "repo": {
                "type": "string",
                "description": "Repository name with owner (e.g., 'owner/repo')",
                "required": True,
            },
            "issue_number": {
                "type": "integer",
                "description": "Issue number",
                "required": True,
            },
        }

    def execute(self, parameters: dict[str, Any]) -> dict[str, Any]:
        repo = self.github.get_repo(parameters["repo"])
        issue = repo.get_issue(parameters["issue_number"])

        return {
            "number": issue.number,
            "title": issue.title,
            "body": issue.body,
            "state": issue.state,
            "user": issue.user.login,
            "created_at": issue.created_at.isoformat(),
            "updated_at": issue.updated_at.isoformat(),
            "comments": issue.comments,
            "labels": [
                {"name": label.name, "color": label.color} for label in issue.labels
            ],
            "assignees": [assignee.login for assignee in issue.assignees],
        }


class AddIssueCommentTool(GitHubTool):
    """Tool for adding a comment to an issue."""

    @property
    def name(self) -> str:
        return "add_issue_comment"

    @property
    def description(self) -> str:
        return "Add a comment to an issue"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "repo": {
                "type": "string",
                "description": "Repository name with owner (e.g., 'owner/repo')",
                "required": True,
            },
            "issue_number": {
                "type": "integer",
                "description": "Issue number",
                "required": True,
            },
            "body": {
                "type": "string",
                "description": "Comment content, supports Markdown",
                "required": True,
            },
        }

    def execute(self, parameters: dict[str, Any]) -> dict[str, Any]:
        repo = self.github.get_repo(parameters["repo"])
        issue = repo.get_issue(parameters["issue_number"])
        comment = issue.create_comment(parameters["body"])

        return {
            "id": comment.id,
            "url": comment.html_url,
        }


class UpdateOrCreateIssueCommentTool(GitHubTool):
    """Tool for updating an existing AI comment on an issue or creating a new one."""

    @property
    def name(self) -> str:
        return "update_or_create_issue_comment"

    @property
    def description(self) -> str:
        return "Update an existing AI comment on an issue or create a new one"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "repo": {
                "type": "string",
                "description": "Repository name with owner (e.g., 'owner/repo')",
                "required": True,
            },
            "issue_number": {
                "type": "integer",
                "description": "Issue number",
                "required": True,
            },
            "body": {
                "type": "string",
                "description": "Comment content, supports Markdown",
                "required": True,
            },
            "header_marker": {
                "type": "string",
                "description": "Unique identifier at the beginning of comments made by this bot",
                "required": True,
            },
        }

    def execute(self, parameters: dict[str, Any]) -> dict[str, Any]:
        repo = self.github.get_repo(parameters["repo"])
        issue = repo.get_issue(parameters["issue_number"])
        comments = list(issue.get_comments())
        header_marker = parameters["header_marker"]

        existing_comment = None
        for comment in comments:
            if comment.body.startswith(header_marker):
                existing_comment = comment
                break

        # Update existing comment or create new one
        if existing_comment:
            existing_comment.edit(parameters["body"])
            return {
                "id": existing_comment.id,
                "url": existing_comment.html_url,
                "action": "updated",
            }
        else:
            # No existing comment found, create a new one
            new_comment = issue.create_comment(parameters["body"])
            return {
                "id": new_comment.id,
                "url": new_comment.html_url,
                "action": "created",
            }


class GetRepositoryFileContentTool(GitHubTool):
    """Tool for getting the content of a file in a repository."""

    @property
    def name(self) -> str:
        return "get_repository_file_content"

    @property
    def description(self) -> str:
        return "Get the content of a file in a repository"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "repo": {
                "type": "string",
                "description": "Repository name with owner (e.g., 'owner/repo')",
                "required": True,
            },
            "path": {
                "type": "string",
                "description": "Path to the file",
                "required": True,
            },
            "ref": {
                "type": "string",
                "description": "The name of the commit/branch/tag",
                "required": False,
            },
        }

    def execute(self, parameters: dict[str, Any]) -> str:
        repo = self.github.get_repo(parameters["repo"])
        path = parameters["path"]
        ref = parameters.get("ref", None)
        try:
            file_content = repo.get_contents(path, ref=ref)
            if isinstance(file_content, list):
                return "This is a directory, not a file"

            return file_content.decoded_content.decode("utf-8")
        except Exception as e:
            return f"Error: {str(e)}"


class GetRepositoryStatsTool(GitHubTool):
    """Tool for getting repository statistics."""

    @property
    def name(self) -> str:
        return "get_repository_stats"

    @property
    def description(self) -> str:
        return "Get statistics about a repository"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "repo": {
                "type": "string",
                "description": "Repository name with owner (e.g., 'owner/repo')",
                "required": True,
            },
        }

    def execute(self, parameters: dict[str, Any]) -> dict[str, Any]:
        repo = self.github.get_repo(parameters["repo"])

        stats = {
            "name": repo.name,
            "full_name": repo.full_name,
            "forks": repo.forks_count,
            "stars": repo.stargazers_count,
            "watchers": repo.watchers_count,
            "open_issues": repo.open_issues_count,
            "network_count": repo.network_count,
            "subscribers_count": repo.subscribers_count,
            "size": repo.size,
            "open_pull_requests": len(list(repo.get_pulls(state="open"))),
        }

        try:
            # These could potentially fail or timeout
            stats["commit_activity"] = (
                [
                    {
                        "week": activity.week,
                        "total": activity.total,
                        "days": activity.days,
                    }
                    for activity in repo.get_stats_commit_activity() or []
                ]
                if repo.get_stats_commit_activity() is not None
                else []
            )

            stats["code_frequency"] = [
                {
                    "week": freq.week,
                    "additions": freq.additions,
                    "deletions": freq.deletions,
                }
                for freq in (repo.get_stats_code_frequency() or [])
            ]
        except:
            stats["commit_activity"] = "Stats unavailable"
            stats["code_frequency"] = "Stats unavailable"

        return stats
