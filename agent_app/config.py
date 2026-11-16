"""Settings read from environment variables / .env (never hard-coded)."""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


class ServiceError(Exception):
    """A Jira, GitHub or LLM call failed. The message is safe to show to the user."""


@dataclass(frozen=True)
class Settings:
    anthropic_api_key: str
    anthropic_model: str
    jira_base_url: str
    jira_email: str
    jira_api_token: str
    github_token: str
    github_repo: str
    github_branch: str
    aut_url: str
    db_path: Path


def normalize_repo(value: str) -> str:
    """Accept 'owner/repo' or a full GitHub URL (with or without .git) and return 'owner/repo'."""
    value = value.strip()
    for prefix in ("https://github.com/", "http://github.com/", "git@github.com:"):
        value = value.removeprefix(prefix)
    return value.removesuffix(".git").strip("/")


def load_settings() -> Settings:
    env = os.environ.get
    return Settings(
        anthropic_api_key=env("ANTHROPIC_API_KEY", ""),
        anthropic_model=env("ANTHROPIC_MODEL", "claude-sonnet-5-5"),
        jira_base_url=env("JIRA_BASE_URL", "").rstrip("/"),
        jira_email=env("JIRA_EMAIL", ""),
        jira_api_token=env("JIRA_API_TOKEN", ""),
        github_token=env("GITHUB_TOKEN", ""),
        github_repo=normalize_repo(env("GITHUB_REPO", "")),
        github_branch=env("GITHUB_BRANCH", "main"),
        aut_url=env("AUT_URL", "http://localhost:8000"),
        db_path=ROOT / "data" / "runs.db",
    )
