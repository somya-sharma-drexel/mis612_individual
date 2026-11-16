"""Execution report: status/pass% rollup (FR-16) and the self-contained HTML report (FR-15)."""
import re
from datetime import datetime

from jinja2 import Environment, select_autoescape


def report_title(jira_key: str, when: datetime) -> str:
    """e.g. 'Execution Report : QA-101-2026-11-14-18:30' (format per the spec example)."""
    return f"Execution Report : {jira_key}-{when:%Y-%m-%d-%H:%M}"


def report_filename(title: str) -> str:
    """Windows forbids ':' in file names, so the title becomes a safe .html name."""
    name = title.replace("Execution Report : ", "Execution Report - ")
    return re.sub(r'[<>:"/\\|?*]', "-", name) + ".html"


def compute_summary(results: list[dict], criteria: list[dict]) -> dict:
    """Overall status, pass %, and a result per acceptance criterion.

    An AC passes only if every test tagged with it passed; an AC with no tests run is "Not run"
    (passed=None). Pass = 100%, Fail = 0%, anything between is Partial.
    """
    run = len(results)
    passed = sum(1 for r in results if r["status"] == "Passed")
    pct = (passed / run * 100) if run else 0.0
    status = "Pass" if run and passed == run else "Fail" if passed == 0 else "Partial"
    ac_rows = []
    for c in criteria:
        tests = [r for r in results if r["ac_id"] == c["id"]]
        ac_rows.append({
            "id": c["id"], "text": c["text"], "tests_run": len(tests),
            "passed": all(t["status"] == "Passed" for t in tests) if tests else None,
        })
    return {"status": status, "pass_pct": round(pct, 1), "tests_run": run, "tests_passed": passed,
            "tests_failed": run - passed, "ac_rows": ac_rows}


_TEMPLATE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>{{ title }}</title>
<style>
body{margin:0;background:#19191B;color:#fff;font-family:system-ui,"Segoe UI",Arial,sans-serif;padding:24px}
h1{font-size:1.5rem;margin:0 0 4px} h2{margin-top:32px}
.meta{color:#8C8E92} .banner{display:inline-block;background:#FF5410;color:#19191B;font-weight:700;
padding:8px 16px;border-radius:4px;margin:16px 0}
table{border-collapse:collapse;width:100%;margin-top:8px}
th,td{border:1px solid #8C8E92;padding:8px;text-align:left;vertical-align:top}
th{background:#8C8E92;color:#19191B} td:first-child{white-space:nowrap} .reason{color:#8C8E92;font-size:.9rem}
</style></head><body>
<h1>{{ title }}</h1>
<div class="meta">{{ jira_key }} &middot; {{ generated }}</div>
<div class="banner">Overall: {{ s.status|upper }} &middot; {{ s.pass_pct }}% ({{ s.tests_passed }} of {{ s.tests_run }} passed)</div>
<h2>Acceptance criteria</h2>
<table><tr><th>Criterion</th><th>Tests run</th><th>Result</th></tr>
{% for a in s.ac_rows %}<tr><td>{{ a.id }}: {{ a.text }}</td><td>{{ a.tests_run }}</td>
<td>{% if a.passed is none %}Not run{% elif a.passed %}&#10004; Passed{% else %}&#10008; Failed{% endif %}</td></tr>
{% endfor %}</table>
<h2>Test cases</h2>
<table><tr><th>ID</th><th>Criterion</th><th>Type</th><th>Scenario</th><th>Result</th></tr>
{% for r in results %}<tr><td>{{ r.tc_id }}</td><td>{{ r.ac_id }}</td><td>{{ r.type }}</td><td>{{ r.title }}</td>
<td>{% if r.status == 'Passed' %}&#10004; Passed{% else %}&#10008; Failed
<div class="reason">{{ r.reason }}</div>{% endif %}</td></tr>
{% endfor %}</table>
</body></html>
"""

_env = Environment(autoescape=select_autoescape(["html"]))


def build_report_html(title: str, jira_key: str, when: datetime, summary: dict, results: list[dict]) -> str:
    return _env.from_string(_TEMPLATE).render(
        title=title, jira_key=jira_key, generated=f"{when:%Y-%m-%d %H:%M}", s=summary, results=results)
