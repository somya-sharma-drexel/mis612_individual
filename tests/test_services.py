"""Unit tests for the Jira, GitHub, LLM and store services using fakes (no network)."""
from types import SimpleNamespace

import pytest
import requests
from github import GithubException, UnknownObjectException

from agent_app.config import ServiceError
from agent_app.services.github_client import GitHubClient
from agent_app.services.jira_client import (
    JiraClient,
    adf_to_text,
    build_comment_adf,
    parse_issue_link,
)
from agent_app.services.llm import LLMClient
from agent_app.services.store import RunStore


# ---------- Jira ----------
@pytest.mark.parametrize("link,expected", [
    ("https://x.atlassian.net/browse/QA-101", ("https://x.atlassian.net", "QA-101")),
    ("https://x.atlassian.net/browse/QA-101?focusedCommentId=5", ("https://x.atlassian.net", "QA-101")),
    ("https://x.atlassian.net/jira/software/projects/QA/boards/1?selectedIssue=QA-7",
     ("https://x.atlassian.net", "QA-7")),
])
def test_parse_issue_link_valid(link, expected):
    assert parse_issue_link(link) == expected


@pytest.mark.parametrize("link", ["", "QA-101", "ftp://x/browse/QA-1", "https://x.atlassian.net/browse/",
                                  "https://x.atlassian.net/jira/software/projects/QA/boards/1"])
def test_parse_issue_link_invalid(link):
    with pytest.raises(ValueError):
        parse_issue_link(link)


def test_adf_to_text_lists_and_paragraphs():
    doc = {"type": "doc", "content": [
        {"type": "paragraph", "content": [{"type": "text", "text": "Criteria:"}]},
        {"type": "bulletList", "content": [
            {"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "A"}]}]},
            {"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "B"}]}]},
        ]},
    ]}
    assert adf_to_text(doc).splitlines() == ["Criteria:", "- A", "- B"]


class FakeResponse:
    def __init__(self, status=200, payload=None, text=""):
        self.status_code, self._payload, self.text = status, payload or {}, text
        self.ok = status < 400

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, response=None, exc=None):
        self.response, self.exc, self.calls, self.auth = response, exc, [], None

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        if self.exc:
            raise self.exc
        return self.response


def _para(text):
    return {"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": text}]}]}


def test_get_issue_reads_description_and_acceptance_field():
    payload = {"key": "QA-101", "names": {"customfield_1": "Acceptance Criteria"},
               "fields": {"summary": "Register", "description": _para("Desc"),
                          "customfield_1": _para("AC text")}}
    client = JiraClient("https://x.atlassian.net", "a@b.c", "tok", session=FakeSession(FakeResponse(payload=payload)))
    issue = client.get_issue("QA-101")
    assert issue == {"key": "QA-101", "summary": "Register", "description": "Desc", "acceptance_field": "AC text"}


@pytest.mark.parametrize("status,fragment", [(401, "credentials"), (404, "not found"), (500, "500")])
def test_jira_errors_are_clear(status, fragment):
    client = JiraClient("https://x.atlassian.net", "a@b.c", "tok", session=FakeSession(FakeResponse(status)))
    with pytest.raises(ServiceError, match=fragment):
        client.get_issue("QA-1")


def test_jira_network_error_is_wrapped():
    client = JiraClient("https://x.atlassian.net", "a@b.c", "tok",
                        session=FakeSession(exc=requests.ConnectionError("down")))
    with pytest.raises(ServiceError, match="Could not reach Jira"):
        client.get_issue("QA-1")


def test_jira_requires_configuration():
    with pytest.raises(ServiceError):
        JiraClient("", "", "")


def test_attach_and_comment_requests(tmp_path):
    session = FakeSession(FakeResponse())
    client = JiraClient("https://x.atlassian.net", "a@b.c", "tok", session=session)
    report = tmp_path / "r.html"
    report.write_text("<html></html>")
    client.attach_file("QA-1", report)
    client.add_comment("QA-1", _para("hi"))
    (m1, u1, k1), (_, u2, k2) = session.calls
    assert (m1, u1.endswith("/issue/QA-1/attachments")) == ("POST", True)
    assert k1["headers"]["X-Atlassian-Token"] == "no-check"
    assert u2.endswith("/issue/QA-1/comment") and k2["json"]["body"]["type"] == "doc"


def test_comment_text_per_status():
    assert adf_to_text(build_comment_adf("Pass", 100, [])).strip() == "ACCEPTANCE CRITERIA FULFILLED. PASSED."
    assert adf_to_text(build_comment_adf("Fail", 0, [])).strip() == "ACCEPTANCE CRITERIA NOT MET. FAILED."
    rows = [{"id": "AC-1", "text": "Valid", "tests_run": 2, "passed": True},
            {"id": "AC-2", "text": "Empty", "tests_run": 3, "passed": False}]
    text = adf_to_text(build_comment_adf("Partial", 60, rows))
    assert "ACCEPTANCE CRITERIA PARTIALLY MET. (60%)" in text
    assert "AC-1: Valid | 2 | Passed" in text and "AC-2: Empty | 3 | Failed" in text


# ---------- GitHub ----------
class FakeRepo:
    def __init__(self, exists):
        self.exists, self.calls = exists, []

    def get_contents(self, path, ref):
        if not self.exists:
            raise UnknownObjectException(404, {}, {})
        return SimpleNamespace(sha="abc")

    def create_file(self, path, message, content, branch):
        self.calls.append(("create", path, message, branch))
        return {"commit": SimpleNamespace(html_url="https://github.com/o/r/commit/1")}

    def update_file(self, path, message, content, sha, branch):
        self.calls.append(("update", path, message, sha))
        return {"commit": SimpleNamespace(html_url="https://github.com/o/r/commit/2")}


def test_push_creates_new_file():
    repo = FakeRepo(exists=False)
    url = GitHubClient("", "", repo=repo).push_feature("QA-101", "Feature: x")
    assert url.endswith("/commit/1")
    assert repo.calls == [("create", "tests/features/QA-101.feature", "Add test cases for QA-101", "main")]


def test_push_updates_existing_file():
    repo = FakeRepo(exists=True)
    url = GitHubClient("", "", repo=repo).push_feature("QA-101", "Feature: x")
    assert url.endswith("/commit/2") and repo.calls[0][0] == "update"


def test_push_to_empty_repo_creates_initial_file():
    repo = FakeRepo(exists=False)

    def empty(path, ref):
        raise GithubException(404, {"message": "This repository is empty."}, {})

    repo.get_contents = empty
    url = GitHubClient("", "", repo=repo).push_feature("QA-1", "x")
    assert url.endswith("/commit/1") and repo.calls[0][0] == "create"


def test_push_failure_is_wrapped():
    repo = FakeRepo(exists=False)
    repo.create_file = lambda *a, **k: (_ for _ in ()).throw(GithubException(403, {"message": "denied"}, {}))
    with pytest.raises(ServiceError, match="403 denied"):
        GitHubClient("", "", repo=repo).push_feature("QA-1", "x")


# ---------- LLM ----------
class FakeAnthropic:
    def __init__(self, tool_input):
        self.messages = self
        self.tool_input, self.kwargs = tool_input, None

    def create(self, **kwargs):
        self.kwargs = kwargs
        content = [] if self.tool_input is None else [
            SimpleNamespace(type="tool_use", name="report_acceptance_criteria", input=self.tool_input)]
        return SimpleNamespace(content=content)


def test_extract_criteria_numbers_and_forces_tool():
    fake = FakeAnthropic({"criteria": ["Valid registration shows HELLO WORLD", "  ", "Empty fields blocked"]})
    out = LLMClient("", "m", client=fake).extract_criteria("S", "D")
    assert out == [{"id": "AC-1", "text": "Valid registration shows HELLO WORLD"},
                   {"id": "AC-2", "text": "Empty fields blocked"}]
    assert fake.kwargs["tool_choice"] == {"type": "auto"}
    assert "report_acceptance_criteria" in fake.kwargs["system"]


def test_llm_missing_structured_answer_raises():
    with pytest.raises(ServiceError, match="retry"):
        LLMClient("", "m", client=FakeAnthropic(None)).extract_criteria("S", "D")


def test_llm_requires_key():
    with pytest.raises(ServiceError):
        LLMClient("", "m")


# ---------- Store ----------
def test_store_roundtrip_and_ordering():
    store = RunStore(":memory:")
    a = store.create_run("QA-1", "https://x/browse/QA-1")
    b = store.create_run("QA-2", "https://x/browse/QA-2")
    store.update_run(a, status="Passed", pass_pct=100.0, commit_url="u")
    store.update_run(a, report_path="r.html")
    run = store.get_run(a)
    assert (run["status"], run["pass_pct"]) == ("Passed", 100.0)
    assert run["data"] == {"commit_url": "u", "report_path": "r.html"}
    assert [r["id"] for r in store.list_runs()] == [b, a]
    with pytest.raises(KeyError):
        store.update_run(999, status="x")


def test_push_file_generic_path_and_message():
    repo = FakeRepo(exists=False)
    url = GitHubClient("", "", repo=repo).push_file("reports/x.html", "<html>", "Add execution report for QA-1")
    assert url.endswith("/commit/1")
    assert repo.calls == [("create", "reports/x.html", "Add execution report for QA-1", "main")]
