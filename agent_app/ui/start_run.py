import streamlit as st

from agent_app import workflow
from agent_app.config import ServiceError
from agent_app.ui.ongoing import resume_run
from agent_app.ui.theme import go, panel, stage_card_html, title_card


def render_start(svc) -> None:
    error = None
    with st.container(key="start_page"):  # one centered column: heading, notice, card, error
        title_card("Start a run")
        ongoing = st.session_state.get("run")
        if workflow.is_ongoing(ongoing):
            with st.container(border=True):
                st.markdown(f"**You have an ongoing run: {ongoing['key']}** · {workflow.ongoing_label(ongoing)}. "
                            "Starting a new run replaces it here (it stays saved in Past runs).")
                st.button("Resume ongoing run", key="start_resume", type="primary", on_click=resume_run)
        with panel("blue", "start"):  # label, text box, Start and Back in one pastel card
            link = st.text_input("Jira ticket link", key="link_input",
                                 placeholder="https://your-domain.atlassian.net/browse/QA-101")
            _, start_col, back_col, _ = st.columns([1.2, 1, 1, 1.2])
            start = start_col.button("Start", key="start_go", type="primary", width="stretch")
            back_col.button("Back", key="back_start", on_click=go, args=("landing",), width="stretch")
        if start:
            try:
                st.session_state.run = workflow.new_run(svc, link)
                for key in ("editing", "edit_problems"):
                    st.session_state.pop(key, None)
            except ValueError as exc:
                error = str(exc)
            else:
                st.session_state.screen = "working"
                st.rerun()
        if error:
            st.error(error)


def render_working(svc) -> None:
    run = st.session_state.run
    title_card(f"Working on {run['key']}")
    ok = failed = False
    steps: list[str] = []
    stages = st.empty()  # the stage card is drawn here once the first stage exists

    def on_step(message: str) -> None:
        steps.append(message)
        stages.html(stage_card_html(steps))

    try:
        workflow.advance_to_review(svc, run, on_step=on_step)
        ok = True
    except ServiceError as exc:
        failed = True
        if steps:
            stages.html(stage_card_html(steps, "failed"))
        st.error(str(exc))
    if ok:
        st.session_state.screen = "review"
        st.rerun()
    if failed:
        left, _ = st.columns([1, 3])
        left.button("Retry", key="retry", type="primary")  # a click reruns the script, resuming the failed step
    st.button("Back", key="back_working", on_click=go, args=("landing",))
