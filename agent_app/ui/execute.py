import html
from pathlib import Path

import streamlit as st

from agent_app import workflow
from agent_app.config import ServiceError
from agent_app.ui.theme import (
    banner,
    go,
    new_run_screen,
    note_card,
    panel,
    result_label,
    stage_card_html,
    title_card,
)


def _no(svc):
    workflow.skip_execution(svc, st.session_state.run)
    st.session_state.screen = "complete"


def render_pushed(svc) -> None:
    run = st.session_state.run
    banner("GITHUB PUSH SUCCESSFUL")
    if run.get("commit_url"):
        url = html.escape(run["commit_url"])
        note_card(f'Commit: <a href="{url}" target="_blank">{url}</a>', "blue")
    with panel("peach", "exec"):
        st.subheader("Do you want to execute the test cases?")
        a, b, _ = st.columns([1, 1, 4])
        a.button("Yes", key="exec_yes", type="primary", on_click=go, args=("select",))
        b.button("No", key="exec_no", on_click=_no, args=(svc,))


def render_select(svc) -> None:
    run = st.session_state.run
    title_card("Run test cases")
    selected = []
    with panel("blue", "select"):
        mode = st.radio("Which test cases?", ["All test cases", "Selected test cases"], key="run_mode")
        run_all = mode == "All test cases"
        for s in workflow.approved(run):
            checked = st.checkbox(f"{s['tc_id']} · {s['title']}  (@{s['ac_id']} @{s['type']})",
                                  value=True, key=f"sel_{s['tc_id']}", disabled=run_all)
            if run_all or checked:
                selected.append(s["tc_id"])
    if st.button("Run tests", key="run_tests", type="primary", disabled=not selected):
        workflow.start_execution(svc, run, selected)  # background thread: survives navigation
        st.session_state.screen = "executing"
        st.rerun()
    st.button("Back", key="back_select", on_click=go, args=("pushed",))


def _progress() -> None:
    """Live stage card; polls every 1.5 seconds and reloads the page when the run changes state."""
    ex = st.session_state.run["exec"]
    card = stage_card_html(ex["steps"], "running" if ex["state"] == "running" else "done")
    if card:  # nothing is shown until the first stage appears
        st.html(card)
    if ex["state"] != "running":
        st.rerun()


def render_executing(svc) -> None:
    run = st.session_state.run
    ex = run["exec"]
    title_card(f"Running tests: {run['key']}")
    if ex["state"] == "done":
        st.session_state.screen = "report"
        st.rerun()
    if ex["state"] == "error":
        st.error(f"{ex['error']} Click Retry to run again.")
        a, b, _ = st.columns([1, 1, 4])
        if a.button("Retry", key="retry_exec", type="primary"):
            workflow.start_execution(svc, run, ex["selected"])
            st.rerun()
        b.button("Back", key="back_exec", on_click=go, args=("select",))
        return
    note_card("You can leave this page: the test run continues in the background. "
              "Find it under ONGOING RUNS in the left menu.", "lilac")
    st.fragment(_progress, run_every=1.5)()
    st.button("Back to dashboard", key="exec_dashboard", on_click=go, args=("landing",))


def render_report(svc) -> None:
    run = st.session_state.run
    summary = run["summary"]
    title_card(run["report_title"])
    banner(f"Overall: {summary['status'].upper()} · {summary['pass_pct']}% "
           f"({summary['tests_passed']} of {summary['tests_run']} passed)")
    with panel("blue", "ac"):
        st.subheader("Acceptance criteria")
        st.table([{"Criterion": f"{a['id']}: {a['text']}", "Tests run": a["tests_run"],
                   "Result": result_label(a["passed"])} for a in summary["ac_rows"]])
    with panel("lilac", "tc"):
        st.subheader("Test cases")
        st.table([{"ID": r["tc_id"], "Criterion": r["ac_id"], "Type": r["type"], "Scenario": r["title"],
                   "Result": result_label(r["status"] == "Passed"), "Failure reason": r["reason"]}
                  for r in run["results"]])
    with open(run["report_path"], "rb") as fh:
        st.download_button("Download report (HTML)", fh.read(), file_name=Path(run["report_path"]).name,
                           mime="text/html", key="download_report")

    with panel("peach", "jira"):
        st.subheader("Do you want to attach this report in Jira?")
        a, b, _ = st.columns([1, 1, 4])
        yes = a.button("Yes", key="jira_yes", type="primary")
        discard = b.button("Discard", key="jira_discard")
    if yes:
        try:
            with st.spinner("Attaching the report and commenting on the Jira ticket"):
                workflow.attach_to_jira(svc, run)
        except ServiceError as exc:
            st.error(f"{exc} Click Yes to retry.")
        else:
            st.session_state.screen = "complete"
            st.rerun()
    if discard:
        workflow.discard(svc, run)
        st.session_state.screen = "complete"
        st.rerun()


def render_complete() -> None:
    run = st.session_state.run
    banner("TEST COMPLETE")
    status = run["status"]
    if status == workflow.REJECTED:
        text = f"{run['key']}: the run was discarded and saved to past runs. Nothing was posted to Jira."
    elif status == workflow.NOT_EXECUTED:
        text = f"{run['key']}: test cases were pushed to GitHub but not executed. Saved to past runs."
    else:
        text = f"{run['key']}: {status} ({run['pass_pct']}%). The report and comment were added to Jira."
    note_card(html.escape(text), "blue")
    a, b, _ = st.columns([1, 1, 3])
    a.button("Start a run", key="complete_start", type="primary", on_click=new_run_screen)
    b.button("View past runs", key="complete_history", on_click=go, args=("history",))
