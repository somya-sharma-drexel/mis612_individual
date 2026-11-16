"""Real write-path smoke test: GitHub push, Jira attachment and Jira comment, each verified by
reading it back and then removed. Usage: python -m scripts.smoke_writes <jira-ticket-link>"""
import sys
import tempfile
from pathlib import Path

from github import Github

from agent_app.config import load_settings
from agent_app.services.github_client import GitHubClient
from agent_app.services.jira_client import (
    JiraClient,
    build_comment_adf,
    parse_issue_link,
)

s = load_settings()
_, key = parse_issue_link(sys.argv[1])
jira = JiraClient(s.jira_base_url, s.jira_email, s.jira_api_token)

# GitHub: create, then update (covers both code paths), verify, delete.
gh = GitHubClient(s.github_token, s.github_repo, s.github_branch)
name = f"{key}-smoke"
print("[GitHub] create:", gh.push_feature(name, "Feature: smoke test\n"))
print("[GitHub] update:", gh.push_feature(name, "Feature: smoke test v2\n"))
repo = Github(s.github_token).get_repo(s.github_repo)
path = f"tests/features/{name}.feature"
f = repo.get_contents(path, ref=s.github_branch)
assert f.decoded_content.decode() == "Feature: smoke test v2\n"
repo.delete_file(path, f"Remove smoke test file for {key}", f.sha, branch=s.github_branch)
print("[GitHub] verified content and deleted test file")

# Jira: attach a file and post a Partial comment (table), verify, delete both.
rows = [{"id": "AC-1", "text": "Valid", "tests_run": 2, "passed": True},
        {"id": "AC-2", "text": "Empty", "tests_run": 3, "passed": False}]
report = Path(tempfile.gettempdir()) / "smoke-report.html"
report.write_text("<html><body>smoke test report</body></html>", encoding="utf-8")
jira.attach_file(key, report)
jira.add_comment(key, build_comment_adf("Partial", 60, rows))
issue = jira._request("GET", f"/issue/{key}", params={"fields": "attachment,comment"}).json()["fields"]
att = [a for a in issue["attachment"] if a["filename"] == report.name]
com = [c for c in issue["comment"]["comments"] if "PARTIALLY MET" in str(c["body"])]
assert att and com, "attachment or comment not found"
print(f"[Jira] attachment ({att[0]['size']} bytes) and comment verified")
for a in att:
    jira._request("DELETE", f"/attachment/{a['id']}")
for c in com:
    jira._request("DELETE", f"/issue/{key}/comment/{c['id']}")
print("[Jira] test attachment and comment deleted")
