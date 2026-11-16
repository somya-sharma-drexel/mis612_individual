"""Sidebar 'ONGOING RUNS' section and the Resume helpers.

While tests execute (on a background thread) the section shows a spinner and polls every 2 seconds,
so it stays live on every page, including the dashboard.
"""
import streamlit as st

from agent_app import workflow

SPINNER = '<span class="spinner" role="status" aria-label="Running tests"></span>'


def resume_run() -> None:
    """Button callback: reopen the ongoing run on the screen it was left on."""
    run = st.session_state.get("run")
    if workflow.is_ongoing(run):
        st.session_state.screen = workflow.resume_screen(run)


def _body() -> None:
    run = st.session_state.get("run")
    if not workflow.is_ongoing(run):
        return
    running = workflow.is_executing(run)
    if running:
        st.session_state["_ongoing_was_running"] = True
    elif st.session_state.pop("_ongoing_was_running", False):
        st.rerun()  # the test run just finished: refresh the whole page once
    if running:
        st.markdown(f'<div class="ongoing-row">{SPINNER}<span>Running tests…</span></div>', unsafe_allow_html=True)
    if st.button(f"{run['key']} · {workflow.ongoing_label(run)}", key="ongoing_open", width="stretch"):
        st.session_state.screen = workflow.resume_screen(run)
        st.rerun()


def render_ongoing() -> None:
    st.markdown('<div class="nav-label">ONGOING RUNS</div>', unsafe_allow_html=True)
    run = st.session_state.get("run")
    if not workflow.is_ongoing(run):
        st.markdown('<span class="muted">No ongoing runs</span>', unsafe_allow_html=True)
        return
    poll = 2 if workflow.is_executing(run) else None
    st.fragment(_body, run_every=poll)()
