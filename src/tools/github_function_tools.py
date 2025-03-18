"""
GitHub tools implemented as function tools for OpenAI Agents SDK.
"""

import logging
from enum import Enum
from typing import (
    Any,
    Dict,
    List,
    NotRequired,
    Optional,
    TypedDict,
)
from agents import RunContextWrapper, function_tool

from src.context.github_context import GithubContext
from github.ContentFile import ContentFile

logger = logging.getLogger("github-tools")


# Pull Request Tools
@function_tool
async def get_pull_request(
    context: RunContextWrapper[GithubContext], repo: str, pr_number: int
) -> Dict[str, Any]:
    """Get detailed information about a pull request.

    Args:
        repo: Repository name with owner (e.g., 'owner/repo')
        pr_number: The number that identifies the pull request

    Returns:
        Dictionary with pull request details including title, body, state, commits, etc.
    """
    logger.info(f"Tool call: get_pull_request repo: {repo}, pr_number: {pr_number}")
    repo_obj = context.context.github_client.get_repo(repo)
    pr = repo_obj.get_pull(pr_number)

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
        "labels": [label.name for label in pr.labels],
        "head": {
            "ref": pr.head.ref,
            "sha": pr.head.sha,
        },
        "base": {
            "ref": pr.base.ref,
            "sha": pr.base.sha,
        },
        "html_url": pr.html_url,
        "draft": pr.draft if hasattr(pr, "draft") else False,
        "milestone": pr.milestone.title if pr.milestone else None,
        "assignees": (
            [assignee.login for assignee in pr.assignees]
            if hasattr(pr, "assignees")
            else []
        ),
        "review_comments": pr.review_comments,
        "maintainer_can_modify": (
            pr.maintainer_can_modify if hasattr(pr, "maintainer_can_modify") else None
        ),
        "mergeable_state": (
            pr.mergeable_state if hasattr(pr, "mergeable_state") else None
        ),
        "merge_commit_sha": (
            pr.merge_commit_sha if hasattr(pr, "merge_commit_sha") else None
        ),
        "closed_at": pr.closed_at.isoformat() if pr.closed_at else None,
        "merged_at": pr.merged_at.isoformat() if pr.merged_at else None,
        "merged_by": pr.merged_by.login if pr.merged_by else None,
        "node_id": pr.node_id if hasattr(pr, "node_id") else None,
    }


@function_tool
async def get_pull_request_files(
    context: RunContextWrapper[GithubContext], repo: str, pr_number: int
) -> List[Dict[str, Any]]:
    """Get files changed in a pull request.

    Args:
        repo: Repository name with owner (e.g., 'owner/repo')
        pr_number: Pull request number

    Returns:
        List of dictionaries with file details including filename, status, changes, etc.
    """
    logger.info(
        f"Tool call: get_pull_request_files repo: {repo}, pr_number: {pr_number}"
    )
    repo_obj = context.context.github_client.get_repo(repo)
    pr = repo_obj.get_pull(pr_number)

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
                "previous_filename": (
                    file.previous_filename
                    if hasattr(file, "previous_filename")
                    else None
                ),
                "sha": file.sha if hasattr(file, "sha") else None,
            }
        )

    return files


@function_tool
async def update_or_create_pr_comment(
    context: RunContextWrapper[GithubContext],
    repo: str,
    pr_number: int,
    body: str,
    header_marker: str,
) -> Dict[str, Any]:
    """Update an existing AI comment or create a new one on a pull request.

    Args:
        repo: Repository name with owner (e.g., 'owner/repo')
        pr_number: Pull request number
        body: Comment content, supports Markdown
        header_marker: Unique identifier at the beginning of comments made by this bot

    Returns:
        Dictionary with comment details including id, url, and action taken ('updated' or 'created')
    """
    logger.info(
        f"Tool call: update_or_create_pr_comment repo: {repo}, pr_number: {pr_number}, body: {body}, header_marker: {header_marker}"
    )
    repo_obj = context.context.github_client.get_repo(repo)
    pr = repo_obj.get_pull(pr_number)
    comments = list(pr.get_issue_comments())

    # Find existing AI review comment
    existing_comment = None
    for comment in comments:
        if comment.body.startswith(header_marker):
            existing_comment = comment
            break

    # Update existing comment or create new one
    if existing_comment:
        existing_comment.edit(body)
        return {
            "id": existing_comment.id,
            "url": existing_comment.html_url,
            "action": "updated",
        }
    else:
        # No existing comment found, create a new one
        new_comment = pr.create_issue_comment(body)
        return {
            "id": new_comment.id,
            "url": new_comment.html_url,
            "action": "created",
        }


@function_tool
async def get_repository_info(
    context: RunContextWrapper[GithubContext], repo: str
) -> Dict[str, Any]:
    """Get basic information about a repository.

    Args:
        repo: Repository name with owner (e.g., 'owner/repo')

    Returns:
        Dictionary with repository details including name, description, language, stars, etc.
    """
    logger.info(f"Tool call: get_repository repo: {repo}")
    repo_obj = context.context.github_client.get_repo(repo)

    return {
        "name": repo_obj.name,
        "full_name": repo_obj.full_name,
        "description": repo_obj.description,
        "language": repo_obj.language,
        "topics": repo_obj.topics,
        "forks": repo_obj.forks_count,
        "stars": repo_obj.stargazers_count,
        "open_issues": repo_obj.open_issues_count,
        "created_at": repo_obj.created_at.isoformat() if repo_obj.created_at else None,
        "updated_at": repo_obj.updated_at.isoformat() if repo_obj.updated_at else None,
        "default_branch": repo_obj.default_branch,
        "license": repo_obj.license.name if repo_obj.license else None,
    }


@function_tool
async def get_issue(
    context: RunContextWrapper[GithubContext], repo: str, issue_number: int
) -> Dict[str, Any]:
    """Get detailed information about an issue.

    Args:
        repo: Repository name with owner (e.g., 'owner/repo')
        issue_number: Issue number

    Returns:
        Dictionary with issue details including title, body, state, comments, labels, etc.
    """
    logger.info(f"Tool call: get_issue repo: {repo}, issue_number: {issue_number}")
    repo_obj = context.context.github_client.get_repo(repo)
    issue = repo_obj.get_issue(issue_number)

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


@function_tool
async def add_issue_comment(
    context: RunContextWrapper[GithubContext],
    repo: str,
    issue_number: int,
    body: str,
) -> Dict[str, Any]:
    """Add a new comment to an issue.

    Args:
        repo: Repository name with owner (e.g., 'owner/repo')
        issue_number: Issue number
        body: Comment content, supports Markdown

    Returns:
        Dictionary with comment details including id and url
    """
    logger.info(
        f"Tool call: add_issue_comment repo: {repo}, issue_number: {issue_number}, body: {body}"
    )
    repo_obj = context.context.github_client.get_repo(repo)
    issue = repo_obj.get_issue(issue_number)
    comment = issue.create_comment(body)
    return {
        "id": comment.id,
        "url": comment.html_url,
    }


@function_tool
async def update_or_create_issue_comment(
    context: RunContextWrapper[GithubContext],
    repo: str,
    issue_number: int,
    body: str,
    header_marker: str,
) -> Dict[str, Any]:
    """Update an existing AI comment on an issue or create a new one.

    Args:
        repo: Repository name with owner (e.g., 'owner/repo')
        issue_number: Issue number
        body: Comment content, supports Markdown
        header_marker: Unique identifier at the beginning of comments made by this bot

    Returns:
        Dictionary with comment details including id, url, and action taken ('updated' or 'created')
    """
    logger.info(
        f"Tool call: update_or_create_issue_comment repo: {repo}, issue_number: {issue_number}, body: {body}, header_marker: {header_marker}"
    )
    repo_obj = context.context.github_client.get_repo(repo)
    issue = repo_obj.get_issue(issue_number)
    comments = list(issue.get_comments())

    existing_comment = None
    for comment in comments:
        if comment.body.startswith(header_marker):
            existing_comment = comment
            break

    # Update existing comment or create new one
    if existing_comment:
        existing_comment.edit(body)
        return {
            "id": existing_comment.id,
            "url": existing_comment.html_url,
            "action": "updated",
        }
    else:
        # No existing comment found, create a new one
        new_comment = issue.create_comment(body)
        return {
            "id": new_comment.id,
            "url": new_comment.html_url,
            "action": "created",
        }


@function_tool
async def get_repository_file_content(
    context: RunContextWrapper[GithubContext],
    repo: str,
    path: str,
    ref: Optional[str] = None,
) -> dict[str, Any]:
    """Get the content of a file or directory in a repository.

    Args:
        repo: Repository name with owner (e.g., 'owner/repo')
        path: Path to the file/directory, empty string for root directory
        ref: The name of the commit/branch/tag, defaults to the default branch

    Returns:
        Dictionary with the content of the file/directory
    """
    logger.info(
        f"Tool call: get_repository_file_content repo: {repo}, path: {path}, ref: {ref}"
    )
    repo_obj = context.context.github_client.get_repo(repo)
    try:
        if ref is None:
            file_content = repo_obj.get_contents(path)
        else:
            file_content = repo_obj.get_contents(path, ref=ref)

        if isinstance(file_content, list):
            return {
                "type": "directory",
                "files": [
                    {
                        "name": file.name,
                        "content": file.decoded_content.decode("utf-8"),
                        "path": file.path,
                        "type": file.type,
                        "size": file.size,
                        "sha": file.sha,
                        "url": file.url,
                        "git_url": file.git_url,
                        "html_url": file.html_url,
                        "download_url": file.download_url,
                    }
                    for file in file_content
                ],
            }
        return {
            "type": file_content.type,
            "content": file_content.decoded_content.decode("utf-8"),
            "path": file_content.path,
            "size": file_content.size,
            "sha": file_content.sha,
            "url": file_content.url,
            "git_url": file_content.git_url,
            "html_url": file_content.html_url,
            "download_url": file_content.download_url,
        }
    except Exception as e:
        return {
            "error": str(e),
            "type": "error",
        }


@function_tool
async def list_repository_files(
    context: RunContextWrapper[GithubContext],
    repo: str,
    path: str | None = None,
    ref: str | None = None,
) -> dict[str, Any]:
    """List files in a repository.

    Args:
        repo: Repository name with owner (e.g., 'owner/repo')
        path: Path to the file/directory, empty string for root directory

    Returns:
        Dictionary with the files in the directory. Includes the type, name, size, sha, url, git_url, html_url, download_url, and path of each file.
    """
    logger.info(f"Tool call: list_repository_files repo: {repo}, path: {path}")
    repo_obj = context.context.github_client.get_repo(repo)
    if ref is not None:
        files = repo_obj.get_contents(path, ref=ref)
    else:
        files = repo_obj.get_contents(path)
    if isinstance(files, list):
        return {
            "type": "directory",
            "files": [
                {
                    "name": file.name,
                    "type": file.type,
                    "size": file.size,
                    "sha": file.sha,
                    "url": file.url,
                    "git_url": file.git_url,
                    "html_url": file.html_url,
                    "download_url": file.download_url,
                    "path": file.path,
                }
                for file in files
            ],
        }
    else:
        return {
            "type": files.type,
            "name": files.name,
            "size": files.size,
            "sha": files.sha,
            "url": files.url,
            "git_url": files.git_url,
            "html_url": files.html_url,
            "download_url": files.download_url,
            "path": files.path,
        }


@function_tool
async def search_code(
    context: RunContextWrapper[GithubContext],
    query: str,
    repo: str,
) -> list[ContentFile]:
    """Search code in a repository with a query.

    Args:
        query: Search query with keywords and qualifiers (supports GitHub search syntax)
        repo: Repository name with owner (e.g., 'owner/repo'). This will appended to the query as a qualifier to limit the search to the specific repository.

    Returns:
        List of ContentFile objects matching the search query
    """
    logger.info(f"Tool call: search_code repo: {repo}, query: {query}")
    query = f"{query} repo:{repo}"
    return context.context.github_client.search_code(query)


@function_tool
async def get_repository_stats(
    context: RunContextWrapper[GithubContext], repo: str
) -> Dict[str, Any]:
    """Get statistical information about a repository.

    Args:
        repo: Repository name with owner (e.g., 'owner/repo')

    Returns:
        Dictionary with repository statistics including forks, stars, commit activity, etc.
    """
    logger.info(f"Tool call: get_repository_stats repo: {repo}")
    repo_obj = context.context.github_client.get_repo(repo)

    stats = {
        "name": repo_obj.name,
        "full_name": repo_obj.full_name,
        "forks": repo_obj.forks_count,
        "stars": repo_obj.stargazers_count,
        "watchers": repo_obj.watchers_count,
        "open_issues": repo_obj.open_issues_count,
        "network_count": repo_obj.network_count,
        "subscribers_count": repo_obj.subscribers_count,
        "size": repo_obj.size,
        "open_pull_requests": len(list(repo_obj.get_pulls(state="open"))),
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
                for activity in repo_obj.get_stats_commit_activity() or []
            ]
            if repo_obj.get_stats_commit_activity() is not None
            else []
        )

        stats["code_frequency"] = [
            {
                "week": freq.week,
                "additions": freq.additions,
                "deletions": freq.deletions,
            }
            for freq in (repo_obj.get_stats_code_frequency() or [])
        ]
    except:
        stats["commit_activity"] = "Stats unavailable"
        stats["code_frequency"] = "Stats unavailable"

    return stats


@function_tool
async def create_issue(
    context: RunContextWrapper[GithubContext],
    repo: str,
    title: str,
    body: str,
    labels: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Create a new issue in a repository.

    Args:
        repo: Repository name with owner (e.g., 'owner/repo')
        title: Issue title
        body: Issue body content, supports Markdown
        labels: Optional list of label names to apply to the issue

    Returns:
        Dictionary with issue details including number, id, url, and title
    """
    logger.info(
        f"Tool call: create_issue repo: {repo}, title: {title}, body: {body}, labels: {labels}"
    )
    repo_obj = context.context.github_client.get_repo(repo)
    issue_labels = labels or []
    issue = repo_obj.create_issue(title=title, body=body, labels=issue_labels)

    return {
        "number": issue.number,
        "id": issue.id,
        "url": issue.html_url,
        "title": issue.title,
    }


class PRReviewEvent(Enum):
    """Pull request review event types."""

    APPROVE = "APPROVE"
    REQUEST_CHANGES = "REQUEST_CHANGES"
    COMMENT = "COMMENT"


class ReviewComment(TypedDict):
    path: str
    body: str
    line: NotRequired[int]
    side: NotRequired[str]


@function_tool
async def create_pull_request_review(
    context: RunContextWrapper[GithubContext],
    repo: str,
    pr_number: int,
    body: str,
    event: PRReviewEvent = PRReviewEvent.COMMENT,
    review_comments: list[ReviewComment] | None = None,
) -> dict[str, Any]:
    """Create a review for a pull request with optional inline comments.

    This function allows you to submit a formal review on a PR with different approval states.
    Use this instead of simple comments when you want to approve, request changes, or provide
    a more structured review with inline comments on specific code sections.

    Args:
        repo: Repository name with owner (e.g., 'owner/repo')
        pr_number: Pull request number
        body: Overall review comment content, supports Markdown. This appears at the top of the review.
        event: Review event type that determines the review action:
            - APPROVE: Approves the PR and allows merging
            - REQUEST_CHANGES: Indicates required changes before the PR can be merged
            - COMMENT: Leaves feedback without explicit approval/rejection (default)
        review_comments: Optional list of ReviewComment objects for inline code comments.
            These appear as comments on specific lines in the PR diff.
            Each ReviewComment object contains:
                - path: The path to the file being commented on
                - body: The comment text
                - line: The line number of the comment (must be part of the diff)
                - side: The side of the diff that the comment applies to (LEFT, RIGHT, or SIDE)

    Returns:
        Dictionary with review details including:
            - id: Unique identifier for the review
            - state: Current state of the review
            - submitted_at: Timestamp when the review was submitted (ISO format)
    """
    logger.info(
        f"Tool call: create_pull_request_review repo: {repo}, pr_number: {pr_number}, body: {body}, event: {event}"
    )
    repo_obj = context.context.github_client.get_repo(repo)
    pr = repo_obj.get_pull(pr_number)

    review_body = body
    if review_comments is None:
        review = pr.create_review(body=review_body, event=event.value)
    else:
        review = pr.create_review(
            body=review_body, event=event.value, comments=review_comments
        )

    return {
        "id": review.id,
        "state": review.state,
        "submitted_at": (
            review.submitted_at.isoformat() if review.submitted_at else None
        ),
    }


@function_tool
async def list_issue_comments(
    context: RunContextWrapper[GithubContext],
    repo: str,
    issue_number: int,
) -> list[dict[str, Any]]:
    """List all comments on an issue.

    Args:
        repo: Repository name with owner (e.g., 'owner/repo')
        issue_number: Issue number

    Returns:
        List of dictionaries with comment details including id, body, user, and timestamps
    """
    logger.info(
        f"Tool call: list_issue_comments repo: {repo}, issue_number: {issue_number}"
    )
    repo_obj = context.context.github_client.get_repo(repo)
    issue = repo_obj.get_issue(issue_number)
    comments = issue.get_comments()

    return [
        {
            "id": comment.id,
            "body": comment.body,
            "user": comment.user.login,
            "created_at": comment.created_at.isoformat(),
            "updated_at": comment.updated_at.isoformat(),
        }
        for comment in comments
    ]


@function_tool
async def add_labels_to_issue(
    context: RunContextWrapper[GithubContext],
    repo: str,
    issue_number: int,
    labels: list[str],
) -> dict[str, Any]:
    """Add labels to an existing issue.

    Args:
        repo: Repository name with owner (e.g., 'owner/repo')
        issue_number: Issue number
        labels: List of label names to add to the issue

    Returns:
        Dictionary with success status
    """
    logger.info(
        f"Tool call: add_labels_to_issue repo: {repo}, issue_number: {issue_number}, labels: {labels}"
    )
    repo_obj = context.context.github_client.get_repo(repo)
    issue = repo_obj.get_issue(issue_number)
    issue.add_to_labels(*labels)
    return {"success": True}


@function_tool
async def list_issue_labels(
    context: RunContextWrapper[GithubContext],
    repo: str,
    issue_number: int,
) -> list[str]:
    """List all labels on an issue.

    Args:
        repo: Repository name with owner (e.g., 'owner/repo')
        issue_number: Issue number

    Returns:
        List of label names on the issue
    """
    logger.info(
        f"Tool call: list_issue_labels repo: {repo}, issue_number: {issue_number}"
    )
    repo_obj = context.context.github_client.get_repo(repo)
    issue = repo_obj.get_issue(issue_number)
    return [label.name for label in issue.labels]
