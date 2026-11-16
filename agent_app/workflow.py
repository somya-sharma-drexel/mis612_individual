"""The run state machine. Pure Python (no Streamlit) so it can be tested directly.

A run is a dict kept in the Streamlit session and mirrored to SQLite at every transition.
Stages: created -> review -> pushed -> select -> report -> complete.

Writes to GitHub and Jira happen ONLY in push_approved, attach_to_jira (human button clicks).
"""
import threading
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from agent_app.config import ServiceError
from agent_app.services.generator import generate_test_cases
from agent_app.services.gherkin import (
    GherkinError,
    parse_scenario,
    render_feature,
    validate_scenario,
)
from agent_app.services.jira_client import build_comment_adf, parse_issue_link
from agent_app.services.report import (
    build_report_html,
    compute_summary,
    report_filename,
    report_title,
)

RUN_SCREENS = ("working", "review", "pushed", "select", "executing", "report")
NOT_EXECUTED = "Pushed – not executed"
REJECTED = "Rejected"


def _save(svc, run: dict, **fields) -> None:
    """Mirror the run to SQLite (FR-21)."""
    svc.store.update_run(
        run["id"], status=run.get("status"), pass_pct=run.get("pass_pct"),
        criteria=run.get("criteria", []), scenarios=run.get("scenarios", []),
        warnings=run.get("warnings", []), uncovered=run.get("uncovered", []),
        summary_text=run.get("issue", {}).get("summary", ""), commit_url=run.get("commit_url"),
        results=run.get("results", []), summary=run.get("summary"),
        report_title=run.get("report_title"), report_path=run.get("report_path"),
        jira_attached=run.get("attached", False), report_commit_url=run.get("report_commit_url"), **fields)


def _set(svc, run: dict, stage: str, status: str | None = None) -> None:
    run["stage"] = stage
    if status:
        run["status"] = status
    _save(svc, run)


# ---------- Start, read, draft (FR-03 to FR-08) ----------
def new_run(svc, link: str) -> dict:
    """Validate the link (FR-03) and create the run. Raises ValueError with a user-facing message."""
    base, key = parse_issue_link(link)
    configured = urlparse(svc.jira_base_url).netloc if svc.jira_base_url else ""
    if configured and urlparse(base).netloc.lower() != configured.lower():
        raise ValueError(f"That link is for a different Jira site than the configured one ({configured}).")
    run_id = svc.store.create_run(key, link.strip(), "Started")
    return {"id": run_id, "link": link.strip(), "key": key, "stage": "created", "status": "Started",
            "criteria": [], "scenarios": [], "warnings": [], "uncovered": [], "pass_pct": None}


def advance_to_review(svc, run: dict, on_step=lambda msg: None) -> None:
    """Read Jira, number the criteria, draft test cases. Idempotent: a retry resumes at the failed step."""
    if "issue" not in run:
        on_step("Reading Jira")
        run["issue"] = svc.jira.get_issue(run["key"])
    if not run["criteria"]:
        on_step("Extracting acceptance criteria")
        issue = run["issue"]
        run["criteria"] = svc.llm.extract_criteria(issue["summary"], issue["description"],
                                                   issue["acceptance_field"])
        if not run["criteria"]:
            raise ServiceError("No acceptance criteria were found in the ticket. Add them to the "
                               "description or an 'Acceptance Criteria' field and try again.")
        _save(svc, run)
    if not run["scenarios"]:
        result = generate_test_cases(svc.llm, run["issue"]["summary"], run["criteria"], on_step=on_step)
        run["scenarios"] = [{**s, "decision": "pending"} for s in result.scenarios]
        run["warnings"], run["uncovered"] = result.warnings, result.uncovered
        if not run["scenarios"]:
            raise ServiceError("No valid test cases could be drafted. Please retry.")
    _set(svc, run, "review", "Drafted")


def regenerate(svc, run: dict) -> None:
    run["scenarios"], run["warnings"], run["uncovered"] = [], [], []
    run["stage"] = "created"


# ---------- Review (FR-09, FR-10) ----------
def find(run: dict, tc_id: str) -> dict:
    return next(s for s in run["scenarios"] if s["tc_id"] == tc_id)


def set_decision(svc, run: dict, tc_id: str, decision: str) -> None:
    assert decision in ("approved", "rejected", "pending")
    find(run, tc_id)["decision"] = decision
    _save(svc, run)


def set_all_decisions(svc, run: dict, decision: str) -> None:
    """Approve all (or reset all to pending) in one step: the review screen's 'Approve all' checkbox."""
    assert decision in ("approved", "pending")
    for s in run["scenarios"]:
        s["decision"] = decision
    _save(svc, run)


def all_approved(run: dict) -> bool:
    return bool(run["scenarios"]) and all(s["decision"] == "approved" for s in run["scenarios"])


def edit_scenario(svc, run: dict, tc_id: str, text: str) -> list[str]:
    """Apply edited Gherkin. Returns problems (empty on success); a saved edit goes back to pending."""
    try:
        parsed = parse_scenario(text)
    except GherkinError as exc:
        return [str(exc)]
    problems = validate_scenario(parsed, {c["id"] for c in run["criteria"]})
    if problems:
        return problems
    s = find(run, tc_id)
    s.update(parsed)
    s["decision"] = "pending"
    _save(svc, run)
    return []


def approved(run: dict) -> list[dict]:
    return [s for s in run["scenarios"] if s["decision"] == "approved"]


def can_push(run: dict) -> bool:
    """FR-10: every test case decided, and at least one approved."""
    return all(s["decision"] != "pending" for s in run["scenarios"]) and bool(approved(run))


def all_rejected(run: dict) -> bool:
    return bool(run["scenarios"]) and all(s["decision"] == "rejected" for s in run["scenarios"])


# ---------- Push (FR-11, FR-12) ----------
def push_approved(svc, run: dict) -> None:
    if not can_push(run):
        raise ServiceError("Approve or reject every test case first.")
    content = render_feature(run["key"], run["issue"]["summary"], approved(run))
    run["commit_url"] = svc.github.push_feature(run["key"], content)
    _set(svc, run, "pushed", "Pushed")


def skip_execution(svc, run: dict) -> None:
    _set(svc, run, "complete", NOT_EXECUTED)


# ---------- Execute and report (FR-13 to FR-16) ----------
def execute(svc, run: dict, selected_ids: list[str], on_step=lambda msg: None) -> None:
    chosen = [s for s in approved(run) if s["tc_id"] in selected_ids]
    if not chosen:
        raise ServiceError("Select at least one test case to run.")
    on_step("Checking the registration page")
    svc.ensure_aut(svc.aut_url)
    on_step(f"Running {len(chosen)} test case(s)")
    run["results"] = svc.run_tests(chosen, svc.aut_url)
    on_step("Building the execution report")
    now = datetime.now()
    run["summary"] = compute_summary(run["results"], run["criteria"])
    run["pass_pct"] = run["summary"]["pass_pct"]
    run["report_title"] = report_title(run["key"], now)
    html = build_report_html(run["report_title"], run["key"], now, run["summary"], run["results"])
    svc.reports_dir.mkdir(parents=True, exist_ok=True)
    path = svc.reports_dir / report_filename(run["report_title"])
    path.write_text(html, encoding="utf-8")
    run["report_path"] = str(path)
    _set(svc, run, "report", "Executed")


# ---------- Jira decision (FR-17 to FR-20) ----------
def attach_to_jira(svc, run: dict) -> None:
    """Yes path: commit the report to GitHub, attach it to the ticket, post the status comment.

    Each finished step is remembered, so a retry after a failure never repeats it.
    """
    if not run.get("report_commit_url"):
        name = Path(run["report_path"]).name.replace(" ", "_")
        html = Path(run["report_path"]).read_text(encoding="utf-8")
        run["report_commit_url"] = svc.github.push_file(
            f"reports/{name}", html, f"Add execution report for {run['key']}")
        _save(svc, run)
    if not run.get("attached"):
        svc.jira.attach_file(run["key"], run["report_path"])
        run["attached"] = True
        _save(svc, run)
    summary = run["summary"]
    svc.jira.add_comment(run["key"], build_comment_adf(summary["status"], summary["pass_pct"], summary["ac_rows"]))
    _set(svc, run, "complete", summary["status"])


def discard(svc, run: dict) -> None:
    """FR-19: mark Rejected and save; nothing is posted to Jira."""
    _set(svc, run, "complete", REJECTED)


# ---------- Ongoing runs and background execution ----------
def is_ongoing(run: dict | None) -> bool:
    """A run is ongoing from the moment it starts until its TEST COMPLETE screen."""
    return bool(run) and run.get("stage") != "complete"


def is_executing(run: dict | None) -> bool:
    ex = (run or {}).get("exec")
    return bool(ex) and ex["state"] == "running"


def start_execution(svc, run: dict, selected_ids: list[str]) -> None:
    """Run the selected tests on a background thread, so the run keeps going while the user is on
    another page. The thread never touches Streamlit; the UI polls run['exec'] for progress."""
    if is_executing(run):
        return
    ex = {"state": "running", "steps": [], "error": None, "selected": list(selected_ids)}
    run["exec"] = ex

    def work():
        try:
            execute(svc, run, selected_ids, on_step=ex["steps"].append)
        except ServiceError as exc:
            ex["error"], ex["state"] = str(exc), "error"
        except Exception as exc:  # noqa: BLE001 - never leave the UI waiting on a dead thread
            ex["error"], ex["state"] = f"Unexpected error: {exc}", "error"
        else:
            ex["state"] = "done"

    ex["thread"] = threading.Thread(target=work, daemon=True)
    ex["thread"].start()


def resume_screen(run: dict) -> str:
    """The screen an ongoing run should reopen on."""
    ex = run.get("exec")
    if run.get("stage") == "report":
        return "report"
    if ex and ex["state"] in ("running", "error"):
        return "executing"
    screen = run.get("screen")
    if screen in RUN_SCREENS and screen != "executing":
        return screen
    return {"created": "working", "review": "review", "pushed": "pushed"}.get(run.get("stage"), "review")


def ongoing_label(run: dict) -> str:
    ex = run.get("exec")
    if is_executing(run):
        return "Running tests"
    if ex and ex["state"] == "error" and run.get("stage") != "report":
        return "Test run failed"
    return {"created": "Drafting test cases", "review": "Reviewing test cases",
            "pushed": "Pushed to GitHub", "report": "Report ready"}.get(run.get("stage"), "In progress")
