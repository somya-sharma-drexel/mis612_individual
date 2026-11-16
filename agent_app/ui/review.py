import streamlit as st

from agent_app import workflow
from agent_app.config import ServiceError
from agent_app.services.gherkin import render_scenario
from agent_app.ui.theme import chip, gherkin_html, go, note_card, panel, title_card

TINT = {"approved": "blue", "rejected": "peach", "pending": "lilac"}
LABELS = {"approved": "✔ Approved", "rejected": "✘ Rejected", "pending": "● Pending"}  # icon + word


def _decide(svc, tc_id, decision):
    workflow.set_decision(svc, st.session_state.run, tc_id, decision)


def _toggle_all(svc):
    """Approve all checkbox: checked approves every test case, unchecked returns them to pending."""
    workflow.set_all_decisions(svc, st.session_state.run,
                               "approved" if st.session_state.approve_all else "pending")


def _start_edit(tc_id):
    st.session_state.editing = tc_id
    st.session_state.pop(f"edit_text_{tc_id}", None)
    st.session_state.pop("edit_problems", None)


def _cancel_edit(tc_id):
    st.session_state.editing = None
    st.session_state.pop(f"edit_text_{tc_id}", None)
    st.session_state.pop("edit_problems", None)


def _save_edit(svc, tc_id):
    problems = workflow.edit_scenario(svc, st.session_state.run, tc_id, st.session_state[f"edit_text_{tc_id}"])
    if problems:
        st.session_state.edit_problems = problems
    else:
        _cancel_edit(tc_id)


def _regenerate(svc):
    workflow.regenerate(svc, st.session_state.run)
    st.session_state.screen = "working"


def render_review(svc) -> None:
    run = st.session_state.run
    title_card(f"Review test cases: {run['key']}", run["issue"]["summary"])

    with st.expander("Acceptance criteria", expanded=True):
        for c in run["criteria"]:
            st.write(f"**{c['id']}** {c['text']}")
    if run["uncovered"]:
        st.warning("No test case could be drafted for: " + ", ".join(run["uncovered"]))
    for w in run["warnings"]:
        st.warning(w)

    # The box mirrors the individual decisions: it is ticked exactly when every case is approved.
    st.session_state.approve_all = workflow.all_approved(run)
    with panel("lilac", "approveall"):
        st.checkbox("Approve all test cases", key="approve_all", on_change=_toggle_all, args=(svc,))

    editing = st.session_state.get("editing")
    for s in run["scenarios"]:
        tc = s["tc_id"]
        with panel(TINT[s["decision"]], f"tc_{tc}"):  # tint follows the decision
            st.markdown(f"**{tc}** &nbsp; {chip(s['decision'], LABELS[s['decision']])}", unsafe_allow_html=True)
            if editing == tc:
                st.text_area("Gherkin", value=render_scenario(s), key=f"edit_text_{tc}", height=220)
                for problem in st.session_state.get("edit_problems", []):
                    st.error(problem)
                a, b, _ = st.columns([1, 1, 4])
                a.button("Save", key=f"save_{tc}", type="primary", on_click=_save_edit, args=(svc, tc))
                b.button("Cancel", key=f"cancel_{tc}", on_click=_cancel_edit, args=(tc,))
            else:
                st.html(gherkin_html(render_scenario(s)))
                a, b, c, _ = st.columns([1.5, 1, 1.3, 2.2])
                a.button("Approve", key=f"approve_{tc}", on_click=_decide, args=(svc, tc, "approved"))
                b.button("Edit", key=f"edit_{tc}", on_click=_start_edit, args=(tc,))
                c.button("Reject", key=f"reject_{tc}", on_click=_decide, args=(svc, tc, "rejected"))

    pending = sum(1 for s in run["scenarios"] if s["decision"] == "pending")
    if workflow.all_rejected(run):
        st.warning("Every test case is rejected, so there is nothing to push.")
        st.button("Regenerate test cases", key="regenerate", on_click=_regenerate, args=(svc,))
    elif pending:
        note_card(f"{pending} test case(s) still need an Approve or Reject decision.", "peach")

    if st.button("OK TO PUSH TO GIT", key="push", type="primary", disabled=not workflow.can_push(run)):
        try:
            with st.spinner("Pushing to GitHub"):
                workflow.push_approved(svc, run)
        except ServiceError as exc:
            st.error(f"{exc} Click OK TO PUSH TO GIT to retry.")
        else:
            st.session_state.screen = "pushed"
            st.rerun()
    st.button("Back", key="back_review", on_click=go, args=("landing",))
