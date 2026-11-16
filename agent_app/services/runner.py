"""Run approved scenarios against the registration page with pytest-bdd + Playwright (FR-14).

pytest runs as a subprocess so Playwright never shares an event loop with Streamlit. Each scenario
gets an extra @TC-n tag in the temporary feature file so results map back to test cases exactly.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from agent_app.config import ROOT, ServiceError
from agent_app.services.gherkin import render_scenario

TIMEOUT_BASE_S = 60
TIMEOUT_PER_TEST_S = 20


def _runtime_feature(scenarios: list[dict]) -> str:
    blocks = []
    for s in scenarios:
        text = render_scenario(s).splitlines()
        text[0] += f" @{s['tc_id']}"
        blocks.append("\n".join(text))
    return "Feature: Execution run\n\n" + "\n\n".join(blocks) + "\n"


def _failure_reason(test: dict) -> str:
    call = test.get("call") or test.get("setup") or {}
    crash = call.get("crash") or {}
    message = crash.get("message") or call.get("longrepr") or "Unknown failure"
    # Keep the first meaningful lines of Playwright's multi-line assertion messages.
    lines = [ln.strip() for ln in str(message).splitlines() if ln.strip()]
    return " ".join(lines[:4])[:400]


def parse_results(report: dict, scenarios: list[dict]) -> list[dict]:
    """Map pytest-json-report output back to the scenarios (matched by the @TC-n marker)."""
    by_tc = {s["tc_id"]: s for s in scenarios}
    results = {}
    for test in report.get("tests", []):
        tc_id = next((k for k in test.get("keywords", []) if k in by_tc), None)
        if tc_id is None:
            continue
        s = by_tc[tc_id]
        passed = test.get("outcome") == "passed"
        duration = sum((test.get(p) or {}).get("duration", 0) for p in ("setup", "call", "teardown"))
        results[tc_id] = {
            "tc_id": tc_id, "ac_id": s["ac_id"], "type": s["type"], "title": s["title"],
            "status": "Passed" if passed else "Failed",
            "reason": "" if passed else _failure_reason(test),
            "duration": round(duration, 2),
        }
    # A scenario that never produced a result (collection error etc.) counts as failed.
    for tc_id, s in by_tc.items():
        results.setdefault(tc_id, {
            "tc_id": tc_id, "ac_id": s["ac_id"], "type": s["type"], "title": s["title"],
            "status": "Failed", "reason": "Test did not run (see runner output).", "duration": 0.0,
        })
    return [results[s["tc_id"]] for s in scenarios]


def run_scenarios(scenarios: list[dict], aut_url: str) -> list[dict]:
    """Execute `scenarios` and return one result dict per scenario, in order."""
    if not scenarios:
        return []
    with tempfile.TemporaryDirectory(prefix="qa_run_") as tmp:
        tmp_path = Path(tmp)
        feature = tmp_path / "run.feature"
        feature.write_text(_runtime_feature(scenarios), encoding="utf-8")
        json_path = tmp_path / "report.json"
        env = {**os.environ, "QA_FEATURE_FILE": str(feature), "AUT_URL": aut_url}
        cmd = [sys.executable, "-m", "pytest", str(ROOT / "tests_runtime" / "test_features.py"),
               "-p", "no:cacheprovider", "-q", "--json-report", f"--json-report-file={json_path}",
               "--json-report-omit=log,warnings,collectors"]
        try:
            proc = subprocess.run(cmd, check=False, cwd=ROOT, env=env, capture_output=True, text=True,
                                  timeout=TIMEOUT_BASE_S + TIMEOUT_PER_TEST_S * len(scenarios))
        except subprocess.TimeoutExpired as exc:
            raise ServiceError("The test run timed out. Is the registration page running?") from exc
        if not json_path.exists():
            tail = (proc.stdout + proc.stderr)[-400:]
            raise ServiceError(f"The test runner produced no results: {tail}")
        report = json.loads(json_path.read_text(encoding="utf-8"))
    return parse_results(report, scenarios)
