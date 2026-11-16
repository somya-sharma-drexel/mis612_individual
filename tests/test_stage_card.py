"""The pastel stage card: hidden until the first stage, then grows with each stage."""
from agent_app.ui.theme import stage_card_html


def test_no_card_before_the_first_stage():
    assert stage_card_html([]) == ""


def test_card_grows_with_each_stage_and_current_one_spins():
    one = stage_card_html(["Checking the registration page"])
    two = stage_card_html(["Checking the registration page", "Running 4 test case(s)"])
    assert one.count('class="stage ') == 1 and two.count('class="stage ') == 2
    assert 'class="spinner"' in one and "stage-now" in one
    assert two.count("stage-done") == 1 and two.count('class="spinner"') == 1  # only the last one spins
    assert "Running 4 test case(s)&hellip;" in two


def test_finished_and_failed_states():
    done = stage_card_html(["a", "b"], "done")
    assert "spinner" not in done and done.count("stage-done") == 2
    failed = stage_card_html(["a", "b"], "failed")
    assert "stage-failed" in failed and "spinner" not in failed and failed.count("stage-done") == 1


def test_stage_text_is_escaped():
    assert "&lt;b&gt;" in stage_card_html(["<b>x</b>"])
