import html

import streamlit as st
import streamlit.components.v1 as components

from agent_app.services.gherkin import render_scenario
from agent_app.ui.theme import (
    chip,
    gherkin_html,
    go,
    note_card,
    panel,
    result_label,
    title_card,
)

RUN_TINT = {"Pass": "blue", "Partial": "lilac", "Fail": "pink"}  # other statuses use peach
DECISION_TINT = {"approved": "blue", "rejected": "peach", "pending": "lilac"}


def _open(run_id):
    st.session_state.history_run = run_id
    st.session_state.screen = "history_detail"


def render_history(svc) -> None:
    with st.container(key="history_page"):  # one centered column, like the other pages
        title_card("Past runs")
        _, back, _ = st.columns([2, 1, 2])
        back.button("Back", key="back_history", on_click=go, args=("landing",), width="stretch")
        runs = svc.store.list_runs()
        if not runs:
            st.info("No runs yet.")
            return
        with panel("lilac", "hist"):  # column titles on a pastel card
            cols = st.columns([2, 2, 2, 3, 2, 2])
            for col, title in zip(cols, ["Jira", "Date", "Time", "Status", "Pass %", ""], strict=True):
                if title:  # an empty "****" would render as a horizontal rule
                    col.markdown(f"**{title}**")
        for r in runs:  # one pastel card per run; the tint follows the status
            with panel(RUN_TINT.get(r["status"], "peach"), f"run_{r['id']}"):
                date, _, time = r["created_at"].partition("T")
                cols = st.columns([2, 2, 2, 3, 2, 2])
                cols[0].write(f"**{r['jira_key']}**")
                cols[1].write(date)
                cols[2].write(time)
                cols[3].write(r["status"])
                cols[4].write("-" if r["pass_pct"] is None else f"{r['pass_pct']:.0f}%")
                cols[5].button("Open", key=f"open_{r['id']}", on_click=_open, args=(r["id"],))


def render_history_detail(svc) -> None:
    r = svc.store.get_run(st.session_state.history_run)
    d = r["data"]
    st.button("Back to past runs", key="back_detail", on_click=go, args=("history",))
    title_card(f"{r['jira_key']} · {r['status']}")
    links = (f"Started {html.escape(r['created_at'].replace('T', ' '))} · "
             f'<a href="{html.escape(r["jira_url"])}" target="_blank">Jira ticket</a>')
    if d.get("commit_url"):
        links += f' · <a href="{html.escape(d["commit_url"])}" target="_blank">GitHub commit</a>'
    note_card(links, "blue")
    if d.get("criteria"):
        with st.expander("Acceptance criteria"):
            for c in d["criteria"]:
                st.write(f"**{c['id']}** {c['text']}")
    title_card("Test cases", kind="blue", level=3)
    results = {x["tc_id"]: x for x in d.get("results", [])}
    for s in d.get("scenarios", []):
        res = results.get(s["tc_id"])
        suffix = f" · {result_label(res['status'] == 'Passed')}" if res else ""
        with panel(DECISION_TINT[s["decision"]], f"h_{s['tc_id']}"):
            st.markdown(f"**{s['tc_id']}** &nbsp; {chip(s['decision'], s['decision'].capitalize())}{suffix}",
                        unsafe_allow_html=True)
            st.html(gherkin_html(render_scenario(s)))
            if res and res["reason"]:
                st.caption(f"Failure reason: {res['reason']}")
    title_card("Report", kind="lilac", level=3)
    path = d.get("report_path")
    try:
        with open(path, encoding="utf-8") as fh:
            components.html(fh.read(), height=700, scrolling=True)
    except (TypeError, OSError):
        st.info("No report for this run.")
