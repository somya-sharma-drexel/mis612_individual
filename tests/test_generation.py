"""Tests for Gherkin rendering/parsing/validation and the generate-repair-coverage loop."""
from types import SimpleNamespace

import pytest

from agent_app.services.generator import generate_test_cases
from agent_app.services.gherkin import (
    GherkinError,
    is_known_step,
    parse_scenario,
    render_feature,
    render_scenario,
    validate_scenario,
)
from agent_app.services.llm import LLMClient

CRITERIA = [{"id": "AC-1", "text": "Valid registration shows HELLO WORLD"},
            {"id": "AC-2", "text": "Empty fields block registration"}]


def sc(ac="AC-1", kind="positive", title="t", steps=None):
    steps = steps or [("Given", "I am on the registration page"),
                      ("When", 'I enter username "alice" and password "password123"'),
                      ("And", "I click Register"), ("Then", 'I should see "HELLO WORLD"')]
    return {"ac_id": ac, "type": kind, "title": title, "steps": [{"keyword": k, "text": t} for k, t in steps]}


@pytest.mark.parametrize("text", [
    "I am on the registration page", 'I enter username ""', 'I enter password "x y"',
    'I enter username "a" and password "b"', "I click Register", 'I should see "HELLO WORLD"',
    'I should not see "HELLO WORLD"', 'I should see an error message containing "required"',
    "I should not see an error message", "the password field should be masked",
    "I should see the Register button",
])
def test_known_steps(text):
    assert is_known_step(text)


@pytest.mark.parametrize("text", ["I log in", 'I enter email "a@b.c"', "I click Submit", 'I should see ""'])
def test_unknown_steps(text):
    assert not is_known_step(text)


def test_validate_valid_and_invalid():
    assert validate_scenario(sc(), {"AC-1"}) == []
    bad = sc(ac="AC-9", kind="weird", steps=[("When", "I log in")])
    problems = " | ".join(validate_scenario(bad, {"AC-1"}))
    for fragment in ("unknown acceptance criterion", "type must be", "not in the allowed vocabulary", "Given"):
        assert fragment in problems


def test_render_parse_roundtrip():
    original = sc(title="Valid registration shows HELLO WORLD")
    text = render_scenario(original)
    assert text.splitlines()[:2] == ["@AC-1 @positive", "Scenario: Valid registration shows HELLO WORLD"]
    assert parse_scenario(text) == original


@pytest.mark.parametrize("text", [
    "Scenario: x\n  Given a", "@AC-1\nScenario: x\n  Given a", "@AC-1 @positive @negative\nScenario: x",
    "@AC-1 @positive\nScenario: x\nScenario: y", "@AC-1 @positive\nScenario: x\n  Nonsense", "",
])
def test_parse_errors(text):
    with pytest.raises(GherkinError):
        parse_scenario(text)


def test_render_feature():
    out = render_feature("QA-1", "Register", [sc(), sc(ac="AC-2", kind="negative", title="n")])
    assert out.startswith("Feature: QA-1 Register\n\n@AC-1 @positive\n")
    assert "\n\n@AC-2 @negative\n" in out and out.endswith("\n")


class ScriptedLLM:
    """Returns pre-scripted batches and records the arguments of each call."""

    def __init__(self, *batches):
        self.batches, self.calls = list(batches), []

    def generate_scenarios(self, summary, criteria, focus_ac_ids=None, feedback=""):
        self.calls.append({"focus": focus_ac_ids, "feedback": feedback})
        return self.batches.pop(0) if self.batches else []


def test_full_coverage_first_try():
    llm = ScriptedLLM([sc("AC-1"), sc("AC-2", "negative", "n")])
    res = generate_test_cases(llm, "S", CRITERIA)
    assert [s["tc_id"] for s in res.scenarios] == ["TC-1", "TC-2"]
    assert res.uncovered == [] and res.warnings == [] and len(llm.calls) == 1


def test_missing_criterion_triggers_follow_up():
    llm = ScriptedLLM([sc("AC-1")], [sc("AC-2", "negative", "n")])
    res = generate_test_cases(llm, "S", CRITERIA)
    assert res.uncovered == [] and len(res.scenarios) == 2
    assert llm.calls[1]["focus"] == ["AC-2"]


def test_gives_up_after_two_follow_ups_and_reports_uncovered():
    llm = ScriptedLLM([sc("AC-1")], [], [])
    res = generate_test_cases(llm, "S", CRITERIA)
    assert res.uncovered == ["AC-2"] and len(llm.calls) == 3


def test_invalid_scenario_is_repaired_once_then_dropped_with_warning():
    bad = sc("AC-2", "negative", "bad", steps=[("Given", "I am on the registration page"), ("When", "I log in")])
    llm = ScriptedLLM([sc("AC-1"), bad], [bad], [])
    res = generate_test_cases(llm, "S", CRITERIA)
    assert "not in the allowed vocabulary" in llm.calls[1]["feedback"]
    assert len(res.warnings) == 1 and "bad" in res.warnings[0]
    assert res.uncovered == ["AC-2"]


def test_duplicates_are_removed():
    llm = ScriptedLLM([sc("AC-1"), sc("AC-1"), sc("AC-2", "negative", "n")])
    assert len(generate_test_cases(llm, "S", CRITERIA).scenarios) == 2


def test_llm_generate_scenarios_prompt_and_schema():
    captured = {}

    class Fake:
        messages = None

        def create(self, **kw):
            captured.update(kw)
            block = SimpleNamespace(type="tool_use", name="report_scenarios", input={"scenarios": [sc()]})
            return SimpleNamespace(content=[block])

    fake = Fake()
    fake.messages = fake
    out = LLMClient("", "m", client=fake).generate_scenarios("S", CRITERIA, focus_ac_ids=["AC-2"], feedback="- x")
    assert out == [sc()]
    assert "I click Register" in captured["system"] and "{{VOCABULARY}}" not in captured["system"]
    user = captured["messages"][0]["content"]
    assert "AC-2: Empty fields block registration" in user and "ONLY for: AC-2" in user and "- x" in user
