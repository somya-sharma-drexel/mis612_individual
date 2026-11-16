"""Service container: real services built lazily from .env, or fakes injected by tests."""
from pathlib import Path

from agent_app.config import load_settings
from agent_app.services.aut import ensure_aut_running
from agent_app.services.github_client import GitHubClient
from agent_app.services.jira_client import JiraClient
from agent_app.services.llm import LLMClient
from agent_app.services.runner import run_scenarios
from agent_app.services.store import RunStore


class Services:
    def __init__(self, settings=None, **overrides):
        self.settings = settings or load_settings()
        s = self.settings
        self.aut_url = overrides.get("aut_url", s.aut_url)
        self.jira_base_url = overrides.get("jira_base_url", s.jira_base_url)
        self.reports_dir: Path = overrides.get("reports_dir", s.db_path.parent / "reports")
        self.store = overrides.get("store") or RunStore(s.db_path)
        self.run_tests = overrides.get("run_tests", run_scenarios)
        self.ensure_aut = overrides.get("ensure_aut", ensure_aut_running)
        self._jira, self._llm, self._github = (overrides.get(k) for k in ("jira", "llm", "github"))

    # Built on first use so a missing credential only breaks the step that needs it.
    @property
    def jira(self):
        if self._jira is None:
            s = self.settings
            self._jira = JiraClient(s.jira_base_url, s.jira_email, s.jira_api_token)
        return self._jira

    @property
    def llm(self):
        if self._llm is None:
            self._llm = LLMClient(self.settings.anthropic_api_key, self.settings.anthropic_model)
        return self._llm

    @property
    def github(self):
        if self._github is None:
            s = self.settings
            self._github = GitHubClient(s.github_token, s.github_repo, s.github_branch)
        return self._github
