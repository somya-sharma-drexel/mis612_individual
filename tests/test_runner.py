"""Integration tests: real browser runs against a good AUT and deliberately broken copies of it."""
import shutil
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

import pytest

from agent_app.services.report import (
    build_report_html,
    compute_summary,
    report_filename,
    report_title,
)
from agent_app.services.runner import run_scenarios

AUT_DIR = Path(__file__).resolve().parent.parent / "aut"
CRITERIA = [
    {"id": "AC-1", "text": "Form elements are shown"},
    {"id": "AC-2", "text": "Password is masked"},
    {"id": "AC-3", "text": "Valid registration shows HELLO WORLD"},
    {"id": "AC-4", "text": "Empty fields block registration"},
    {"id": "AC-5", "text": "Short password blocks registration"},
]
GIVEN = ("Given", "I am on the registration page")


def sc(tc, ac, kind, title, *steps):
    return {"tc_id": tc, "ac_id": ac, "type": kind, "title": title,
            "steps": [{"keyword": k, "text": t} for k, t in (GIVEN, *steps)]}


SCENARIOS = [
    sc("TC-1", "AC-1", "positive", "Elements shown", ("Then", "I should see the Username field"),
       ("And", "I should see the Password field"), ("And", "I should see the Register button")),
    sc("TC-2", "AC-2", "positive", "Masked", ("When", 'I enter password "secret123"'),
       ("Then", "the password field should be masked")),
    sc("TC-3", "AC-3", "positive", "Valid", ("When", 'I enter username "alice" and password "securePass123"'),
       ("And", "I click Register"), ("Then", 'I should see "HELLO WORLD"'),
       ("And", "I should not see an error message")),
    sc("TC-4", "AC-3", "boundary", "Eight chars accepted",
       ("When", 'I enter username "alice" and password "abcd1234"'),
       ("And", "I click Register"), ("Then", 'I should see "HELLO WORLD"')),
    sc("TC-5", "AC-4", "negative", "Empty username", ("When", 'I enter password "securePass123"'),
       ("And", "I click Register"), ("Then", 'I should not see "HELLO WORLD"'),
       ("And", 'I should see an error message containing "username"')),
    sc("TC-6", "AC-4", "edge", "Both empty", ("When", "I click Register"),
       ("Then", 'I should not see "HELLO WORLD"')),
    sc("TC-7", "AC-5", "negative", "Three chars rejected",
       ("When", 'I enter username "alice" and password "abc"'), ("And", "I click Register"),
       ("Then", 'I should not see "HELLO WORLD"')),
    sc("TC-8", "AC-5", "boundary", "Seven chars rejected",
       ("When", 'I enter username "alice" and password "abcd123"'), ("And", "I click Register"),
       ("Then", 'I should not see "HELLO WORLD"')),
]


def serve(directory: Path, port: int):
    proc = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1",
                             "--directory", str(directory)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(50):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}", timeout=1)
            return proc
        except OSError:
            time.sleep(0.1)
    proc.terminate()
    raise RuntimeError("test server did not start")


@pytest.fixture(scope="module")
def good_url():
    proc = serve(AUT_DIR, 8011)
    yield "http://127.0.0.1:8011"
    proc.terminate()


@pytest.fixture(scope="module")
def short_password_bug_url(tmp_path_factory):
    d = tmp_path_factory.mktemp("bug_len")
    shutil.copytree(AUT_DIR, d / "aut")
    js = d / "aut" / "app.js"
    js.write_text(js.read_text().replace("MIN_PASSWORD_LENGTH = 8", "MIN_PASSWORD_LENGTH = 6"))
    proc = serve(d / "aut", 8012)
    yield "http://127.0.0.1:8012"
    proc.terminate()


@pytest.fixture(scope="module")
def accept_all_bug_url(tmp_path_factory):
    d = tmp_path_factory.mktemp("bug_all")
    shutil.copytree(AUT_DIR, d / "aut")
    js = d / "aut" / "app.js"
    js.write_text(js.read_text().replace("function validate(username, password) {",
                                         "function validate(username, password) {\n  return null;"))
    proc = serve(d / "aut", 8013)
    yield "http://127.0.0.1:8013"
    proc.terminate()


def test_all_pass_on_good_aut(good_url):
    start = time.time()
    results = run_scenarios(SCENARIOS, good_url)
    assert [r["status"] for r in results] == ["Passed"] * 8, results
    assert time.time() - start < 120
    summary = compute_summary(results, CRITERIA)
    assert (summary["status"], summary["pass_pct"]) == ("Pass", 100.0)
    assert all(row["passed"] for row in summary["ac_rows"])


def test_partial_when_boundary_bug(short_password_bug_url):
    results = {r["tc_id"]: r for r in run_scenarios(SCENARIOS, short_password_bug_url)}
    assert results["TC-8"]["status"] == "Failed" and results["TC-8"]["reason"]
    assert results["TC-7"]["status"] == "Passed"
    summary = compute_summary(list(results.values()), CRITERIA)
    assert summary["status"] == "Partial" and summary["pass_pct"] == 87.5
    ac = {r["id"]: r["passed"] for r in summary["ac_rows"]}
    assert ac["AC-5"] is False and ac["AC-3"] is True


def test_fail_when_nothing_passes(accept_all_bug_url):
    negatives = [s for s in SCENARIOS if s["ac_id"] in ("AC-4", "AC-5")]
    results = run_scenarios(negatives, accept_all_bug_url)
    assert all(r["status"] == "Failed" for r in results)
    summary = compute_summary(results, CRITERIA)
    assert summary["status"] == "Fail" and summary["pass_pct"] == 0.0
    assert {r["id"]: r["passed"] for r in summary["ac_rows"]}["AC-1"] is None  # not run


def test_report_and_names(good_url):
    results = run_scenarios(SCENARIOS[:2], good_url)
    when = datetime(2026, 11, 14, 18, 30)
    title = report_title("QA-101", when)
    assert title == "Execution Report : QA-101-2026-11-14-18:30"
    assert ":" not in report_filename(title) and report_filename(title).endswith(".html")
    html = build_report_html(title, "QA-101", when, compute_summary(results, CRITERIA), results)
    assert title in html and "Passed" in html and "Not run" in html and "100.0%" in html
