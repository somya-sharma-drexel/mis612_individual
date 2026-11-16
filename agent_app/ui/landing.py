import streamlit as st

from agent_app import workflow
from agent_app.ui.charts import count_statuses, status_donut
from agent_app.ui.ongoing import SPINNER, resume_run
from agent_app.ui.theme import chip, go, new_run_screen, panel, stat_card, title_card


def render_landing(svc) -> None:
    runs = svc.store.list_runs()
    passed = sum(1 for r in runs if r["status"] == "Pass")
    attention = sum(1 for r in runs if r["status"] in ("Partial", "Fail"))

    with st.container(key="hero"):  # heading, subheading and the two buttons are centered
        title_card("QA Test Case Generator Agent",
                   "Turn a Jira story into approved test cases, a GitHub push, a test run and a Jira report.",
                   level=1)
        _, left, right, _ = st.columns([1, 1, 1, 1])
        left.button("Start a run", key="start_run", type="primary", on_click=new_run_screen, width="stretch")
        right.button("View past runs", key="view_runs", on_click=go, args=("history",), width="stretch")

    ongoing = st.session_state.get("run")
    if workflow.is_ongoing(ongoing):
        st.write("")
        with st.container(border=True):
            spin = SPINNER + " " if workflow.is_executing(ongoing) else ""
            st.markdown(f"{spin}**Ongoing run: {ongoing['key']}** &nbsp; "
                        f"<span class='muted'>{workflow.ongoing_label(ongoing)}</span>", unsafe_allow_html=True)
            st.button("Resume run", key="resume_dash", type="primary", on_click=resume_run)

    st.write("")
    c1, c2, c3 = st.columns(3)
    c1.markdown(stat_card("peach", "Total runs", len(runs), "All time"), unsafe_allow_html=True)
    c2.markdown(stat_card("blue", "Passed", passed, "100% of tests passed"), unsafe_allow_html=True)
    c3.markdown(stat_card("pink", "Needs attention", attention, "Partial or failed"), unsafe_allow_html=True)

    st.write("")
    recent, chart = st.columns([3, 2])
    with recent, panel("blue", "dash_recent"):
        st.subheader("Recent runs")
        if not runs:
            st.markdown('<span class="muted">No runs yet. Start one to see it here.</span>', unsafe_allow_html=True)
        for r in runs[:5]:
            date, _, time = r["created_at"].partition("T")
            pct = "-" if r["pass_pct"] is None else f"{r['pass_pct']:.0f}%"
            st.markdown(f"**{r['jira_key']}** &nbsp; {chip('pending', r['status'])} &nbsp; "
                        f"<span class='muted'>{date} {time} · {pct}</span>", unsafe_allow_html=True)
    with chart, panel("lilac", "dash_chart"):
        st.subheader("Run results")
        counts = count_statuses(runs)
        st.markdown(status_donut(counts), unsafe_allow_html=True)
        if not sum(counts.values()):
            st.markdown('<span class="muted">Pass, partial and fail runs will appear here.</span>',
                        unsafe_allow_html=True)
