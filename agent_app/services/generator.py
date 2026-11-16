"""Draft test cases and make sure every acceptance criterion is covered (FR-06 to FR-08)."""
from dataclasses import dataclass, field

from agent_app.services.gherkin import validate_scenario

MAX_COVERAGE_RETRIES = 2


@dataclass
class GenerationResult:
    scenarios: list[dict] = field(default_factory=list)  # each has a "tc_id" like "TC-1"
    uncovered: list[str] = field(default_factory=list)  # AC ids still without a scenario
    warnings: list[str] = field(default_factory=list)  # dropped scenarios etc., shown to the user


def _dedupe_key(s: dict) -> tuple:
    return (s["ac_id"], s["type"], tuple((x["keyword"], x["text"]) for x in s["steps"]))


def generate_test_cases(llm, summary: str, criteria: list[dict], on_step=lambda msg: None) -> GenerationResult:
    """Draft scenarios, repair invalid ones once, then fill coverage gaps (max 2 more calls)."""
    ac_ids = {c["id"] for c in criteria}
    result = GenerationResult()
    seen: set[tuple] = set()

    def accept(raw: list[dict]) -> list[str]:
        """Keep valid new scenarios; return feedback lines for the invalid ones."""
        feedback = []
        for s in raw:
            problems = validate_scenario(s, ac_ids)
            if problems:
                feedback.append(f"- {s.get('title', '(untitled)')!r} ({s.get('ac_id')}): " + "; ".join(problems))
            elif _dedupe_key(s) not in seen:
                seen.add(_dedupe_key(s))
                result.scenarios.append(s)
        return feedback

    on_step("Drafting test cases")
    feedback = accept(llm.generate_scenarios(summary, criteria))
    if feedback:
        on_step("Repairing invalid test cases")
        feedback = accept(llm.generate_scenarios(summary, criteria, feedback="\n".join(feedback)))
    for line in feedback:
        result.warnings.append(f"Dropped an invalid test case: {line[2:]}")

    for _ in range(MAX_COVERAGE_RETRIES):
        missing = [c["id"] for c in criteria if c["id"] not in {s["ac_id"] for s in result.scenarios}]
        if not missing:
            break
        on_step(f"Checking coverage: drafting more for {', '.join(missing)}")
        accept(llm.generate_scenarios(summary, criteria, focus_ac_ids=missing))

    covered = {s["ac_id"] for s in result.scenarios}
    result.uncovered = [c["id"] for c in criteria if c["id"] not in covered]
    for i, s in enumerate(result.scenarios, 1):
        s["tc_id"] = f"TC-{i}"
    return result
