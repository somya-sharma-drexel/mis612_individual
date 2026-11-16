"""Claude API wrapper. Every call is answered through a tool so the output is schema-shaped JSON."""
from pathlib import Path

import anthropic

from agent_app.config import ServiceError
from agent_app.services.gherkin import KEYWORDS, TYPES, vocabulary_text

MAX_TOKENS = 4096

_CRITERIA_TOOL = {
    "name": "report_acceptance_criteria",
    "description": "Report the acceptance criteria found in a Jira ticket, one string per criterion.",
    "input_schema": {
        "type": "object",
        "properties": {
            "criteria": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Each distinct, testable acceptance criterion, in order. Empty if none are stated.",
            }
        },
        "required": ["criteria"],
    },
}

_CRITERIA_SYSTEM = (
    "You extract acceptance criteria from Jira tickets. Use only criteria the ticket states or "
    "clearly implies as acceptance conditions. Split compound criteria into separate items only "
    "when they are independently testable. Do not invent criteria."
)


_SCENARIOS_TOOL = {
    "name": "report_scenarios",
    "description": "Report the drafted Gherkin scenarios.",
    "input_schema": {
        "type": "object",
        "properties": {
            "scenarios": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "ac_id": {"type": "string", "description": "e.g. AC-2"},
                        "type": {"type": "string", "enum": list(TYPES)},
                        "title": {"type": "string"},
                        "steps": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "keyword": {"type": "string", "enum": list(KEYWORDS)},
                                    "text": {"type": "string"},
                                },
                                "required": ["keyword", "text"],
                            },
                        },
                    },
                    "required": ["ac_id", "type", "title", "steps"],
                },
            }
        },
        "required": ["scenarios"],
    },
}

_PROMPT_DIR = Path(__file__).resolve().parent.parent / "prompts"


def _generation_system_prompt() -> str:
    template = (_PROMPT_DIR / "generate_gherkin.md").read_text(encoding="utf-8")
    return template.replace("{{VOCABULARY}}", vocabulary_text())


class LLMClient:
    def __init__(self, api_key: str, model: str, client=None):
        """`client` can be injected for tests."""
        if client is None:
            if not api_key:
                raise ServiceError("Claude is not configured. Set ANTHROPIC_API_KEY in .env.")
            client = anthropic.Anthropic(api_key=api_key)
        self._client = client
        self._model = model

    def structured(self, system: str, user: str, tool: dict) -> dict:
        """Call the model, forcing it to answer through `tool`; return the tool input dict."""
        try:
            resp = self._client.messages.create(
                model=self._model,
                max_tokens=MAX_TOKENS,
                system=f"{system}\n\nAnswer by calling the {tool['name']} tool exactly once.",
                messages=[{"role": "user", "content": user}],
                tools=[tool],
                tool_choice={"type": "auto"},  # this model rejects forced tool use
            )
        except anthropic.AuthenticationError as exc:
            raise ServiceError("Claude rejected the API key (check ANTHROPIC_API_KEY).") from exc
        except anthropic.APIError as exc:
            raise ServiceError(f"Claude API call failed: {exc}") from exc
        for block in resp.content:
            if block.type == "tool_use" and block.name == tool["name"]:
                return dict(block.input)
        raise ServiceError("Claude did not return the expected structured answer. Please retry.")

    def extract_criteria(self, summary: str, description: str, acceptance_field: str = "") -> list[dict]:
        """Return numbered criteria [{"id": "AC-1", "text": ...}, ...] (FR-04, FR-05)."""
        parts = [f"Summary: {summary}"]
        if acceptance_field:
            parts.append(f"Acceptance Criteria field:\n{acceptance_field}")
        parts.append(f"Description:\n{description or '(empty)'}")
        result = self.structured(_CRITERIA_SYSTEM, "\n\n".join(parts), _CRITERIA_TOOL)
        texts = [t.strip() for t in result.get("criteria", []) if isinstance(t, str) and t.strip()]
        return [{"id": f"AC-{i}", "text": t} for i, t in enumerate(texts, 1)]

    def generate_scenarios(self, summary: str, criteria: list[dict], focus_ac_ids: list[str] | None = None,
                           feedback: str = "") -> list[dict]:
        """Draft raw scenarios (FR-06, FR-07). `focus_ac_ids` limits the request to some criteria
        (used to fill coverage gaps); `feedback` lists problems from an earlier attempt to fix."""
        listing = "\n".join(f"{c['id']}: {c['text']}" for c in criteria)
        user = f"Ticket summary: {summary}\n\nAcceptance criteria:\n{listing}\n"
        if focus_ac_ids:
            user += f"\nWrite scenarios ONLY for: {', '.join(focus_ac_ids)}.\n"
        if feedback:
            user += f"\nYour previous attempt had these problems, fix them:\n{feedback}\n"
        result = self.structured(_generation_system_prompt(), user, _SCENARIOS_TOOL)
        return [s for s in result.get("scenarios", []) if isinstance(s, dict)]
