"""Gherkin scenarios: the fixed step vocabulary, rendering, parsing and validation.

The vocabulary is shared with the Phase 4 step definitions: every step the agent may generate
must match one of STEP_PATTERNS, so every generated scenario is executable.
"""
import re

KEYWORDS = ("Given", "When", "Then", "And", "But")
TYPES = ("positive", "negative", "boundary", "edge")

# (regex matched against the step text with fullmatch, human-readable form shown to the LLM)
STEP_VOCABULARY = [
    (r'I am on the registration page', 'I am on the registration page'),
    (r'I enter username "([^"]*)"', 'I enter username "<text>"'),
    (r'I enter password "([^"]*)"', 'I enter password "<text>"'),
    (r'I enter username "([^"]*)" and password "([^"]*)"', 'I enter username "<text>" and password "<text>"'),
    (r'I click Register', 'I click Register'),
    (r'I should see "([^"]+)"', 'I should see "<text>"'),
    (r'I should not see "([^"]+)"', 'I should not see "<text>"'),
    (r'I should see an error message containing "([^"]+)"', 'I should see an error message containing "<text>"'),
    (r'I should not see an error message', 'I should not see an error message'),
    (r'the password field should be masked', 'the password field should be masked'),
    (r'I should see the (Username field|Password field|Register button)',
     'I should see the <Username field | Password field | Register button>'),
]
STEP_PATTERNS = [re.compile(p) for p, _ in STEP_VOCABULARY]


class GherkinError(ValueError):
    """A scenario is malformed or uses a step outside the vocabulary."""


def vocabulary_text() -> str:
    return "\n".join(f"- {human}" for _, human in STEP_VOCABULARY)


def is_known_step(text: str) -> bool:
    return any(p.fullmatch(text) for p in STEP_PATTERNS)


def validate_scenario(scenario: dict, valid_ac_ids: set[str] | None = None) -> list[str]:
    """Return a list of problems (empty if the scenario is valid)."""
    problems = []
    if valid_ac_ids is not None and scenario.get("ac_id") not in valid_ac_ids:
        problems.append(f"unknown acceptance criterion {scenario.get('ac_id')!r}")
    if scenario.get("type") not in TYPES:
        problems.append(f"type must be one of {', '.join(TYPES)}")
    title = scenario.get("title", "")
    if not title.strip() or "\n" in title:
        problems.append("title must be a single non-empty line")
    steps = scenario.get("steps") or []
    if not steps:
        problems.append("no steps")
    for step in steps:
        if step.get("keyword") not in KEYWORDS:
            problems.append(f"bad keyword {step.get('keyword')!r}")
        if not is_known_step(step.get("text", "")):
            problems.append(f"step not in the allowed vocabulary: {step.get('text')!r}")
    if steps and steps[0].get("keyword") != "Given":
        problems.append("first step must start with Given")
    return problems


def render_scenario(scenario: dict) -> str:
    lines = [f"@{scenario['ac_id']} @{scenario['type']}", f"Scenario: {scenario['title']}"]
    lines += [f"  {s['keyword']} {s['text']}" for s in scenario["steps"]]
    return "\n".join(lines)


def parse_scenario(text: str) -> dict:
    """Parse the text of one scenario (as shown in the Edit box) back into a dict.

    Raises GherkinError on any structural problem. Vocabulary is checked by validate_scenario.
    """
    tags, title, steps = [], None, []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("@"):
            if title is not None:
                raise GherkinError("Tags must come before the Scenario line.")
            tags += line.split()
        elif line.startswith("Scenario:"):
            if title is not None:
                raise GherkinError("Only one Scenario per test case.")
            title = line[len("Scenario:"):].strip()
        else:
            keyword, _, rest = line.partition(" ")
            if title is None or keyword not in KEYWORDS or not rest:
                raise GherkinError(f"Unrecognised line: {line!r}")
            steps.append({"keyword": keyword, "text": rest.strip()})
    if title is None:
        raise GherkinError("Missing 'Scenario:' line.")
    ac = [t[1:] for t in tags if re.fullmatch(r"@AC-\d+", t)]
    kinds = [t[1:] for t in tags if t[1:] in TYPES]
    if len(ac) != 1:
        raise GherkinError("Exactly one @AC-n tag is required.")
    if len(kinds) != 1:
        raise GherkinError(f"Exactly one type tag is required ({', '.join('@' + t for t in TYPES)}).")
    return {"ac_id": ac[0], "type": kinds[0], "title": title, "steps": steps}


def render_feature(jira_key: str, summary: str, scenarios: list[dict]) -> str:
    """The .feature file content for the approved scenarios."""
    header = f"Feature: {jira_key} {summary}".strip()
    return header + "\n\n" + "\n\n".join(render_scenario(s) for s in scenarios) + "\n"
