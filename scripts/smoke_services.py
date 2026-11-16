"""Smoke-test the real services with the credentials in .env.

Read-only by default: reads the Jira ticket, extracts criteria with Claude, opens the GitHub repo.
Pass --push-test to also commit tests/features/<KEY>-smoke.feature to GitHub (a real write).

Usage (from the project root):
    python -m scripts.smoke_services https://your-domain.atlassian.net/browse/QA-101 [--push-test]
"""
import sys

from agent_app.config import ServiceError, load_settings
from agent_app.services.generator import generate_test_cases
from agent_app.services.gherkin import render_scenario
from agent_app.services.github_client import GitHubClient
from agent_app.services.jira_client import JiraClient, parse_issue_link
from agent_app.services.llm import LLMClient


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 2
    s = load_settings()
    try:
        _, key = parse_issue_link(args[0])
        issue = JiraClient(s.jira_base_url, s.jira_email, s.jira_api_token).get_issue(key)
        print(f"[Jira] {issue['key']}: {issue['summary']}")
        criteria = LLMClient(s.anthropic_api_key, s.anthropic_model).extract_criteria(
            issue["summary"], issue["description"], issue["acceptance_field"])
        print(f"[Claude] {len(criteria)} criteria")
        for c in criteria:
            print(f"   {c['id']}: {c['text']}")
        llm = LLMClient(s.anthropic_api_key, s.anthropic_model)
        result = generate_test_cases(llm, issue["summary"], criteria, on_step=lambda m: print(f"[Agent] {m}"))
        for sc in result.scenarios:
            print(f"\n{sc['tc_id']}\n{render_scenario(sc)}")
        print(f"\n[Agent] uncovered: {result.uncovered or 'none'}; warnings: {result.warnings or 'none'}")
        gh = GitHubClient(s.github_token, s.github_repo, s.github_branch)
        print(f"[GitHub] repo {s.github_repo} reachable")
        if "--push-test" in sys.argv:
            url = gh.push_feature(f"{key}-smoke", "Feature: smoke test\n")
            print(f"[GitHub] committed: {url}")
    except (ServiceError, ValueError) as exc:
        print(f"FAILED: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
