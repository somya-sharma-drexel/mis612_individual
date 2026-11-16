"""Workflow logic tests with fake services."""
from pathlib import Path

import pytest

from agent_app import workflow
from agent_app.config import ServiceError
from tests.fakes import LINK, build_services


@pytest.fixture()
def svc(tmp_path):
    return build_services(tmp_path)


def drafted(svc):
    run = workflow.new_run(svc, LINK)
    workflow.advance_to_review(svc, run)
    return run


@pytest.mark.parametrize("link", ["", "nonsense", "https://example.atlassian.net/jira/boards",
                                  "https://other.atlassian.net/browse/QA-1"])
def test_new_run_rejects_bad_links(svc, link):
    with pytest.raises(ValueError):
        workflow.new_run(svc, link)
    assert svc.store.list_runs() == []


def test_draft_numbers_criteria_and_tcs(svc):
    run = drafted(svc)
    assert [c["id"] for c in run["criteria"]] == ["AC-1", "AC-2"]
    assert [s["tc_id"] for s in run["scenarios"]] == ["TC-1", "TC-2", "TC-3", "TC-4"]
    assert run["stage"] == "review" and svc.store.get_run(run["id"])["status"] == "Drafted"


def test_advance_resumes_after_failure(svc):
    svc.jira.fail_issue = 1
    run = workflow.new_run(svc, LINK)
    with pytest.raises(ServiceError):
        workflow.advance_to_review(svc, run)
    workflow.advance_to_review(svc, run)  # retry succeeds
    assert run["stage"] == "review"


def test_push_gated_until_every_case_decided(svc):
    run = drafted(svc)
    assert not workflow.can_push(run)
    for tc in ("TC-1", "TC-2", "TC-3"):
        workflow.set_decision(svc, run, tc, "approved")
    assert not workflow.can_push(run)  # TC-4 still pending
    with pytest.raises(ServiceError):
        workflow.push_approved(svc, run)
    assert svc.github.pushes == []
    workflow.set_decision(svc, run, "TC-4", "rejected")
    assert workflow.can_push(run)


def test_approve_all_enables_push_and_can_be_undone(svc):
    run = drafted(svc)
    workflow.set_decision(svc, run, "TC-2", "rejected")
    workflow.set_all_decisions(svc, run, "approved")
    assert workflow.all_approved(run) and workflow.can_push(run)
    assert all(s["decision"] == "approved" for s in svc.store.get_run(run["id"])["data"]["scenarios"])
    workflow.set_all_decisions(svc, run, "pending")
    assert not workflow.all_approved(run) and not workflow.can_push(run)


def test_all_rejected_cannot_push(svc):
    run = drafted(svc)
    for s in run["scenarios"]:
        workflow.set_decision(svc, run, s["tc_id"], "rejected")
    assert workflow.all_rejected(run) and not workflow.can_push(run)


def test_edit_scenario(svc):
    run = drafted(svc)
    workflow.set_decision(svc, run, "TC-1", "approved")
    ok = "@AC-1 @edge\nScenario: Edited\n  Given I am on the registration page\n  When I click Register"
    assert workflow.edit_scenario(svc, run, "TC-1", ok) == []
    s = workflow.find(run, "TC-1")
    assert (s["title"], s["type"], s["decision"]) == ("Edited", "edge", "pending")
    assert workflow.edit_scenario(svc, run, "TC-1", "garbage")
    bad = "@AC-1 @edge\nScenario: x\n  Given I am on the registration page\n  When I log in"
    assert "vocabulary" in workflow.edit_scenario(svc, run, "TC-1", bad)[0]
    assert workflow.edit_scenario(svc, run, "TC-1", ok.replace("@AC-1", "@AC-9"))  # unknown criterion


def full_run(svc, failing_run=False):
    run = drafted(svc)
    for tc, decision in (("TC-1", "approved"), ("TC-2", "approved"), ("TC-3", "approved"), ("TC-4", "rejected")):
        workflow.set_decision(svc, run, tc, decision)
    workflow.push_approved(svc, run)
    return run


def test_push_contains_only_approved(svc):
    run = full_run(svc)
    key, content = svc.github.pushes[0]
    assert key == "QA-1" and "Valid registration" in content and "Empty username" in content
    assert "Both empty" not in content
    assert run["stage"] == "pushed" and run["commit_url"].endswith("/1")


def test_execute_runs_only_selected_and_builds_report(svc):
    run = full_run(svc)
    workflow.execute(svc, run, ["TC-1", "TC-3"])
    assert svc.run_tests.ran == [["TC-1", "TC-3"]]
    assert run["summary"]["status"] == "Pass" and run["stage"] == "report"
    assert run["report_title"].startswith("Execution Report : QA-1-")
    assert Path(run["report_path"]).read_text(encoding="utf-8").startswith("<!DOCTYPE html>")
    with pytest.raises(ServiceError):
        workflow.execute(svc, run, ["TC-4"])  # rejected case cannot be run


def test_attach_to_jira_writes_and_sets_final_status(svc):
    run = full_run(svc)
    workflow.execute(svc, run, ["TC-1", "TC-2", "TC-3"])
    assert svc.jira.writes() == []  # nothing before the click
    workflow.attach_to_jira(svc, run)
    assert svc.jira.writes() == [("attach", "QA-1"), ("comment", "QA-1")]
    stored = svc.store.get_run(run["id"])
    assert (stored["status"], stored["pass_pct"]) == ("Pass", 100.0)
    assert stored["data"]["commit_url"] and stored["data"]["report_path"] and stored["data"]["jira_attached"]


def test_yes_path_commits_report_to_repo(svc):
    run = full_run(svc)
    workflow.execute(svc, run, ["TC-1", "TC-2", "TC-3"])
    assert not any(p.startswith("reports/") for p in svc.github.files)
    workflow.attach_to_jira(svc, run)
    report_paths = [p for p in svc.github.files if p.startswith("reports/")]
    assert len(report_paths) == 1 and " " not in report_paths[0] and report_paths[0].endswith(".html")
    assert svc.store.get_run(run["id"])["data"]["report_commit_url"]


def test_discard_commits_no_report(svc):
    run = full_run(svc)
    workflow.execute(svc, run, ["TC-1", "TC-2", "TC-3"])
    workflow.discard(svc, run)
    assert not any(p.startswith("reports/") for p in svc.github.files)


def test_attach_retry_does_not_duplicate_attachment(svc):
    run = full_run(svc)
    workflow.execute(svc, run, ["TC-1", "TC-2", "TC-3"])
    svc.jira.fail_comment = 1
    with pytest.raises(ServiceError):
        workflow.attach_to_jira(svc, run)
    workflow.attach_to_jira(svc, run)
    assert [c[0] for c in svc.jira.writes()].count("attach") == 1


def test_discard_posts_nothing_and_is_saved(svc):
    run = full_run(svc)
    workflow.execute(svc, run, ["TC-1", "TC-2", "TC-3"])
    workflow.discard(svc, run)
    assert svc.jira.writes() == []
    assert svc.store.get_run(run["id"])["status"] == "Rejected"


def test_no_to_execute_status(svc):
    run = full_run(svc)
    workflow.skip_execution(svc, run)
    assert svc.store.get_run(run["id"])["status"] == "Pushed – not executed"


def test_background_execution_reaches_done_and_report(svc):
    run = full_run(svc)
    assert workflow.is_ongoing(run) and not workflow.is_executing(run)
    workflow.start_execution(svc, run, ["TC-1", "TC-2"])
    run["exec"]["thread"].join(timeout=30)
    assert run["exec"]["state"] == "done" and run["stage"] == "report"
    assert run["exec"]["steps"][0] == "Checking the registration page"
    assert workflow.resume_screen(run) == "report" and workflow.ongoing_label(run) == "Report ready"


def test_background_execution_error_is_reported_and_retryable(svc):
    run = full_run(svc)
    workflow.start_execution(svc, run, ["TC-4"])  # TC-4 is rejected: nothing runnable
    run["exec"]["thread"].join(timeout=30)
    assert run["exec"]["state"] == "error" and "Select at least one" in run["exec"]["error"]
    assert workflow.resume_screen(run) == "executing" and workflow.ongoing_label(run) == "Test run failed"
    workflow.start_execution(svc, run, ["TC-1"])
    run["exec"]["thread"].join(timeout=30)
    assert run["exec"]["state"] == "done"


def test_second_start_while_running_is_ignored(svc):
    import threading

    gate = threading.Event()
    inner = svc.run_tests
    svc.run_tests = lambda s, u: (gate.wait(30), inner(s, u))[1]
    run = full_run(svc)
    workflow.start_execution(svc, run, ["TC-1"])
    first = run["exec"]
    assert workflow.is_executing(run) and workflow.ongoing_label(run) == "Running tests"
    workflow.start_execution(svc, run, ["TC-2"])
    assert run["exec"] is first
    gate.set()
    first["thread"].join(timeout=30)


def test_resume_screen_and_labels_by_stage(svc):
    run = drafted(svc)
    assert workflow.resume_screen(run) == "review" and workflow.ongoing_label(run) == "Reviewing test cases"
    run["screen"] = "select"
    run["stage"] = "pushed"
    assert workflow.resume_screen(run) == "select" and workflow.ongoing_label(run) == "Pushed to GitHub"
    run["stage"] = "complete"
    assert not workflow.is_ongoing(run)
