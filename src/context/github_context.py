from typing import Any

from github import Github
from pydantic import BaseModel, ConfigDict


class GithubContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    github_event: dict[str, Any]
    github_client: Github
