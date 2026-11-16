"""Streamlit entry point: routes between the run-workflow screens."""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # so `agent_app` imports work

from agent_app import workflow
from agent_app.deps import Services
from agent_app.ui import execute, history, landing, review, start_run
from agent_app.ui.theme import apply_theme, render_sidebar

st.set_page_config(page_title="QA Test Case Generator Agent", layout="wide")


@st.cache_resource
def _real_services() -> Services:
    return Services()


def get_services():
    """Tests inject fakes through st.session_state['_services']."""
    override = st.session_state.get("_services")
    return override if override is not None else _real_services()


svc = get_services()
st.session_state.setdefault("screen", "landing")
screen = st.session_state.screen

# A run screen with no run (for example after a browser refresh) falls back to the landing page.
if screen in (*workflow.RUN_SCREENS, "complete") and not st.session_state.get("run"):
    screen = st.session_state.screen = "landing"

if screen in workflow.RUN_SCREENS:
    st.session_state.run["screen"] = screen  # lets the sidebar reopen the run where it was left
apply_theme(screen)
render_sidebar()

if screen == "landing":
    landing.render_landing(svc)
elif screen == "start":
    start_run.render_start(svc)
elif screen == "working":
    start_run.render_working(svc)
elif screen == "review":
    review.render_review(svc)
elif screen == "pushed":
    execute.render_pushed(svc)
elif screen == "select":
    execute.render_select(svc)
elif screen == "executing":
    execute.render_executing(svc)
elif screen == "report":
    execute.render_report(svc)
elif screen == "complete":
    execute.render_complete()
elif screen == "history":
    history.render_history(svc)
elif screen == "history_detail":
    history.render_history_detail(svc)
