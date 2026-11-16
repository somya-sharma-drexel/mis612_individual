"""End-to-end UI tests with Streamlit's AppTest and fake services."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from tests.fakes import LINK, build_services

APP = str(Path(__file__).resolve().parent.parent / "agent_app" / "app.py")


@pytest.fixture()
def svc(tmp_path):
    return build_services(tmp_path, failing=("TC-3",))


def new_app(svc):
    at = AppTest.from_file(APP, default_timeout=30)
    at.session_state["_services"] = svc
    at.run()
    assert not at.exception
    return at


def click(at, key):
    at.button(key=key).click().run()
    assert not at.exception, at.exception


def start_to_review(at):
    click(at, "start_run")
    at.text_input(key="link_input").input(LINK).run()
    click(at, "start_go")


def finish_execution(at):
    """Tests run on a background thread: wait for it, then let the page notice."""
    at.session_state["run"]["exec"]["thread"].join(timeout=30)
    at.run()
    assert not at.exception, at.exception


def banners(at):
    return " ".join(m.value for m in at.markdown)


def test_landing_has_two_buttons_and_nav(svc):
    at = new_app(svc)
    keys = {b.key for b in at.button}
    assert {"start_run", "view_runs"} <= keys  # FR-01
    assert {"nav_home", "nav_start", "nav_history"} <= keys  # sidebar navigation


def test_sidebar_nav_reaches_history_and_start(svc):
    at = new_app(svc)
    click(at, "nav_history")
    assert "Past runs" in page_html(at)
    click(at, "nav_start")
    assert any(b.key == "start_go" for b in at.button)


def test_invalid_link_shows_error_and_stays(svc):
    at = new_app(svc)
    click(at, "start_run")
    at.text_input(key="link_input").input("not a link").run()
    click(at, "start_go")
    assert at.error and "Jira" in at.error[0].value
    assert any(b.key == "start_go" for b in at.button)


def test_full_yes_path_with_edit_and_reject(svc):
    at = new_app(svc)
    start_to_review(at)
    assert at.button(key="push").disabled  # nothing decided yet (FR-10)

    click(at, "edit_TC-4")
    at.text_area(key="edit_text_TC-4").input("garbage").run()
    click(at, "save_TC-4")
    assert at.error  # invalid edit is explained
    at.text_area(key="edit_text_TC-4").input(
        "@AC-2 @edge\nScenario: Both empty edited\n  Given I am on the registration page\n  When I click Register"
    ).run()
    click(at, "save_TC-4")
    for tc in ("TC-1", "TC-2", "TC-3", "TC-4"):
        assert any(b.key == f"approve_{tc}" for b in at.button)
    for tc in ("TC-1", "TC-2", "TC-3"):
        click(at, f"approve_{tc}")
    assert at.button(key="push").disabled  # TC-4 still pending after its edit
    click(at, "reject_TC-4")
    assert not at.button(key="push").disabled

    click(at, "push")
    assert "GITHUB PUSH SUCCESSFUL" in banners(at)
    assert svc.github.pushes and "Both empty" not in svc.github.pushes[0][1]

    click(at, "exec_yes")
    at.radio(key="run_mode").set_value("Selected test cases").run()
    at.checkbox(key="sel_TC-2").set_value(False).run()
    click(at, "run_tests")
    finish_execution(at)
    assert svc.run_tests.ran == [["TC-1", "TC-3"]]
    assert "Overall: PARTIAL" in banners(at)
    assert svc.jira.writes() == []  # nothing in Jira before the click

    click(at, "jira_yes")
    assert "TEST COMPLETE" in banners(at)
    assert svc.jira.writes() == [("attach", "QA-1"), ("comment", "QA-1")]

    click(at, "complete_history")
    assert any(b.key.startswith("open_") for b in at.button)
    assert "Partial" in " ".join(str(c.value) for c in at.get("markdown"))


def test_approve_all_checkbox(svc):
    at = new_app(svc)
    start_to_review(at)
    assert not at.checkbox(key="approve_all").value and at.button(key="push").disabled
    at.checkbox(key="approve_all").check().run()
    assert not at.exception and at.checkbox(key="approve_all").value
    assert not at.button(key="push").disabled  # every case approved at once
    # An individual change unticks the box; ticking again approves everything.
    click(at, "reject_TC-2")
    assert not at.checkbox(key="approve_all").value
    at.checkbox(key="approve_all").check().run()
    assert at.checkbox(key="approve_all").value and not at.button(key="push").disabled
    at.checkbox(key="approve_all").uncheck().run()  # unticking returns all to pending
    assert at.button(key="push").disabled


def test_discard_path(svc):
    at = new_app(svc)
    start_to_review(at)
    for tc in ("TC-1", "TC-2", "TC-3", "TC-4"):
        click(at, f"approve_{tc}")
    click(at, "push")
    click(at, "exec_yes")
    click(at, "run_tests")
    finish_execution(at)
    click(at, "jira_discard")
    assert "TEST COMPLETE" in banners(at)
    assert svc.jira.writes() == []
    assert svc.store.list_runs()[0]["status"] == "Rejected"


def test_no_to_execute_path(svc):
    at = new_app(svc)
    start_to_review(at)
    for tc in ("TC-1", "TC-2", "TC-3", "TC-4"):
        click(at, f"approve_{tc}")
    click(at, "push")
    click(at, "exec_no")
    assert "TEST COMPLETE" in banners(at)
    assert svc.store.list_runs()[0]["status"] == "Pushed – not executed"


def test_all_rejected_disables_push_and_offers_regenerate(svc):
    at = new_app(svc)
    start_to_review(at)
    for tc in ("TC-1", "TC-2", "TC-3", "TC-4"):
        click(at, f"reject_{tc}")
    assert at.button(key="push").disabled
    assert any(b.key == "regenerate" for b in at.button)


def test_push_failure_shows_error_and_allows_retry(svc):
    at = new_app(svc)
    start_to_review(at)
    for tc in ("TC-1", "TC-2", "TC-3", "TC-4"):
        click(at, f"approve_{tc}")
    svc.github.fail = True
    click(at, "push")
    assert at.error and "retry" in at.error[0].value.lower()
    svc.github.fail = False
    click(at, "push")
    assert "GITHUB PUSH SUCCESSFUL" in banners(at)


def test_jira_read_failure_shows_retry(svc):
    svc.jira.fail_issue = 1
    at = new_app(svc)
    click(at, "start_run")
    at.text_input(key="link_input").input(LINK).run()
    click(at, "start_go")
    assert at.error and any(b.key == "retry" for b in at.button)
    click(at, "retry")
    assert any(b.key == "approve_TC-1" for b in at.button)


def page_html(at):
    return " ".join(str(h.value) for h in at.html)


def sidebar_text(at):
    return " ".join(str(m.value) for m in at.sidebar.markdown)


def test_review_cards_show_colored_gherkin(svc):
    at = new_app(svc)
    start_to_review(at)
    html = " ".join(str(h.value) for h in at.html)
    assert html.count('<pre class="gherkin"') == 4 and "g-kw" in html and "g-tag" in html


def test_ongoing_run_can_be_reopened_from_sidebar_and_dashboard(svc):
    at = new_app(svc)
    assert "No ongoing runs" in sidebar_text(at)
    start_to_review(at)
    click(at, "approve_TC-1")
    click(at, "back_review")  # leave the run: dashboard
    assert any(b.key == "resume_dash" for b in at.button)  # dashboard card
    ongoing = [b for b in at.sidebar.button if b.key == "ongoing_open"]
    assert ongoing and "QA-1" in ongoing[0].label and "Reviewing test cases" in ongoing[0].label
    click(at, "ongoing_open")
    assert any(b.key == "approve_TC-2" for b in at.button)  # back on the review screen
    assert "approved" in at.session_state["run"]["scenarios"][0]["decision"]  # nothing was lost
    click(at, "nav_home")
    click(at, "resume_dash")
    assert any(b.key == "approve_TC-2" for b in at.button)


def test_start_screen_warns_about_ongoing_run_and_can_resume(svc):
    at = new_app(svc)
    start_to_review(at)
    click(at, "nav_start")
    assert any(b.key == "start_resume" for b in at.button)
    click(at, "start_resume")
    assert any(b.key == "approve_TC-1" for b in at.button)


def test_spinner_in_sidebar_while_tests_execute_and_run_survives_navigation(tmp_path):
    import threading

    from tests.fakes import build_services, make_run_tests

    gate, inner = threading.Event(), make_run_tests()

    def slow(scenarios, url):
        gate.wait(30)
        return inner(scenarios, url)

    svc = build_services(tmp_path, run_tests=slow)
    at = new_app(svc)
    start_to_review(at)
    at.checkbox(key="approve_all").check().run()
    click(at, "push")
    click(at, "exec_yes")
    click(at, "run_tests")  # starts the background run; page shows the progress screen
    assert "Running tests: QA-1" in page_html(at)
    click(at, "nav_home")  # leave while it runs
    assert 'class="spinner"' in sidebar_text(at) and "Running tests" in sidebar_text(at)
    gate.set()
    at.session_state["run"]["exec"]["thread"].join(timeout=30)
    at.run()
    ongoing = [b for b in at.sidebar.button if b.key == "ongoing_open"]
    assert 'class="spinner"' not in sidebar_text(at) and "Report ready" in ongoing[0].label
    click(at, "ongoing_open")
    assert "Overall: PASS" in banners(at)


def test_past_runs_shows_one_card_per_run(svc):
    for key in ("QA-7", "QA-8", "QA-9"):
        svc.store.create_run(key, f"https://example.atlassian.net/browse/{key}", "Pass")
    at = new_app(svc)
    click(at, "nav_history")
    opens = [b.key for b in at.button if b.key.startswith("open_")]
    assert len(opens) == 3  # one Open button, inside its own card, per run


def test_executing_page_shows_stage_card(tmp_path):
    import threading

    from tests.fakes import build_services, make_run_tests

    gate, inner = threading.Event(), make_run_tests()
    svc = build_services(tmp_path, run_tests=lambda s, u: (gate.wait(30), inner(s, u))[1])
    at = new_app(svc)
    start_to_review(at)
    at.checkbox(key="approve_all").check().run()
    click(at, "push")
    click(at, "exec_yes")
    click(at, "run_tests")
    cards = [h.value for h in at.html if "stage-card" in str(h.value)]
    assert cards and "Running 4 test case(s)" in cards[-1] and "Checking the registration page" in cards[-1]
    gate.set()
    at.session_state["run"]["exec"]["thread"].join(timeout=30)


def test_page_text_is_shown_on_pastel_cards(svc):
    at = new_app(svc)
    assert "pcard-grey" in page_html(at) and "QA Test Case Generator Agent" in page_html(at)
    start_to_review(at)
    html = page_html(at)
    assert "pcard-grey" in html and "Review test cases: QA-1" in html and "User can register" in html
    at.checkbox(key="approve_all").check().run()
    click(at, "push")
    assert "pcard-blue" in page_html(at) and "github.com/o/r/commit" in page_html(at)  # commit link card
    click(at, "exec_yes")
    assert "Run test cases" in page_html(at)  # title card on the select page


def test_past_runs_and_detail_use_pastel_cards(svc):
    run_id = svc.store.create_run("QA-5", "https://example.atlassian.net/browse/QA-5", "Pass")
    svc.store.update_run(run_id, status="Pass", pass_pct=100.0, scenarios=[], criteria=[])
    at = new_app(svc)
    click(at, "nav_history")
    assert "pcard-grey" in page_html(at) and "Past runs" in page_html(at)
    click(at, f"open_{run_id}")
    html = page_html(at)
    assert "QA-5 · Pass" in html and "pcard-blue" in html and "Jira ticket" in html and "pcard-lilac" in html


def test_no_black_cards_remain_on_the_main_screens(svc):
    from agent_app.ui import history, review
    from agent_app.ui.theme import CSS

    assert 'st-key-card_' not in CSS  # the black-card rules are gone
    assert 'class="stage-card"' not in CSS and "background: #0A0A0A" not in CSS.split("/* Hover and keyboard focus")[0]
    # Card tints follow the decision / status, always one of the pastel kinds.
    assert set(review.TINT.values()) <= {"pink", "peach", "blue", "lilac"}
    assert set(history.RUN_TINT.values()) <= {"pink", "peach", "blue", "lilac"}
    at = new_app(svc)
    start_to_review(at)
    assert "pcard-grey" in page_html(at)  # page heading card
