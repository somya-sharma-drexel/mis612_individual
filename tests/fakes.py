"""Fake Jira / LLM / GitHub / runner for workflow and UI tests (no network, no browser)."""
from agent_app.config import ServiceError
from agent_app.deps import Services
from agent_app.services.store import RunStore

LINK = "https://example.atlassian.net/browse/QA-1"
GIVEN = {"keyword": "Given", "text": "I am on the registration page"}


def scenario(ac, kind, title, *steps):
    return {"ac_id": ac, "type": kind, "title": title,
            "steps": [GIVEN] + [{"keyword": k, "text": t} for k, t in steps]}


RAW_SCENARIOS = [
    scenario("AC-1", "positive", "Valid registration", ("When", 'I enter username "alice" and password "password123"'),
             ("And", "I click Register"), ("Then", 'I should see "HELLO WORLD"')),
    scenario("AC-1", "boundary", "Eight chars accepted", ("When", 'I enter username "alice" and password "12345678"'),
             ("And", "I click Register"), ("Then", 'I should see "HELLO WORLD"')),
    scenario("AC-2", "negative", "Empty username", ("When", 'I enter password "password123"'),
             ("And", "I click Register"), ("Then", 'I should not see "HELLO WORLD"')),
    scenario("AC-2", "edge", "Both empty", ("When", "I click Register"), ("Then", 'I should not see "HELLO WORLD"')),
]


class FakeJira:
    def __init__(self):
        self.calls, self.fail_issue, self.fail_comment = [], 0, 0

    def get_issue(self, key):
        self.calls.append(("get_issue", key))
        if self.fail_issue:
            self.fail_issue -= 1
            raise ServiceError("Jira is down")
        return {"key": key, "summary": "User can register", "description": "d", "acceptance_field": ""}

    def attach_file(self, key, path):
        self.calls.append(("attach", key))

    def add_comment(self, key, body):
        self.calls.append(("comment", key))
        if self.fail_comment:
            self.fail_comment -= 1
            raise ServiceError("Jira comment failed")
        self.last_comment = body

    def writes(self):
        return [c for c in self.calls if c[0] in ("attach", "comment")]


class FakeLLM:
    def extract_criteria(self, summary, description, acceptance_field=""):
        return [{"id": "AC-1", "text": "Valid registration shows HELLO WORLD"},
                {"id": "AC-2", "text": "Empty fields block registration"}]

    def generate_scenarios(self, summary, criteria, focus_ac_ids=None, feedback=""):
        return [dict(s) for s in RAW_SCENARIOS]


class FakeGitHub:
    def __init__(self):
        self.pushes, self.fail = [], False

    def push_feature(self, key, content):
        return self.push_file(f"tests/features/{key}.feature", content, f"Add test cases for {key}")

    def push_file(self, path, content, message):
        if self.fail:
            raise ServiceError("GitHub push failed")
        self.files = getattr(self, "files", {})
        self.files[path] = content
        if path.startswith("tests/features/"):
            self.pushes.append((path.split("/")[-1].removesuffix(".feature"), content))
        return f"https://github.com/o/r/commit/{len(self.files)}"


def make_run_tests(failing=()):
    ran = []

    def run_tests(scenarios, url):
        ran.append([s["tc_id"] for s in scenarios])
        return [{"tc_id": s["tc_id"], "ac_id": s["ac_id"], "type": s["type"], "title": s["title"],
                 "status": "Failed" if s["tc_id"] in failing else "Passed",
                 "reason": "boom" if s["tc_id"] in failing else "", "duration": 0.1} for s in scenarios]

    run_tests.ran = ran
    return run_tests


def build_services(tmp_path, failing=(), run_tests=None):
    svc = Services(jira=FakeJira(), llm=FakeLLM(), github=FakeGitHub(), store=RunStore(":memory:"),
                   reports_dir=tmp_path / "reports", run_tests=run_tests or make_run_tests(failing),
                   ensure_aut=lambda url: None, jira_base_url="https://example.atlassian.net",
                   aut_url="http://localhost:8000")
    return svc
