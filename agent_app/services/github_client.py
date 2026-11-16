"""GitHub: commit the .feature file. Only call from the OK TO PUSH TO GIT handler."""
from github import Github, GithubException, UnknownObjectException

from agent_app.config import ServiceError


class EmptyRepoError(Exception):
    """Internal marker: the repository has no commits yet, so the file cannot exist."""


class GitHubClient:
    def __init__(self, token: str, repo_name: str, branch: str = "main", repo=None):
        """`repo` can be injected for tests; otherwise it is looked up with PyGithub."""
        self.branch = branch
        if repo is not None:
            self._repo = repo
            return
        if not (token and repo_name):
            raise ServiceError("GitHub is not configured. Set GITHUB_TOKEN and GITHUB_REPO in .env.")
        try:
            self._repo = Github(token).get_repo(repo_name)
        except GithubException as exc:
            raise ServiceError(f"Could not open GitHub repo {repo_name}: {_reason(exc)}") from exc

    def _get_existing(self, path):
        try:
            return self._repo.get_contents(path, ref=self.branch)
        except GithubException as exc:
            # A repo with no commits answers 404 "This repository is empty." instead of "not found".
            if exc.status == 404 and "empty" in str(getattr(exc, "data", "")).lower():
                raise EmptyRepoError from exc
            raise

    def push_feature(self, jira_key: str, content: str) -> str:
        """Create or update tests/features/<KEY>.feature; return the commit URL."""
        return self.push_file(f"tests/features/{jira_key}.feature", content, f"Add test cases for {jira_key}")

    def push_file(self, path: str, content: str, message: str) -> str:
        """Create or update one text file on the configured branch; return the commit URL."""
        try:
            try:
                existing = self._get_existing(path)
            except (UnknownObjectException, EmptyRepoError):
                result = self._repo.create_file(path, message, content, branch=self.branch)
            else:
                result = self._repo.update_file(path, message, content, existing.sha, branch=self.branch)
        except GithubException as exc:
            raise ServiceError(f"GitHub push failed: {_reason(exc)}") from exc
        return result["commit"].html_url


def _reason(exc: GithubException) -> str:
    data = exc.data if isinstance(exc.data, dict) else {}
    return f"{exc.status} {data.get('message', '')}".strip()
