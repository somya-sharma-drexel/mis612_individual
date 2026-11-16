"""Jira Cloud REST v3: read a ticket, attach the report, add the status comment.

Writes (attach_file, add_comment) must only be called from a user-approved button handler.
"""
import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests

from agent_app.config import ServiceError

_KEY_RE = re.compile(r"[A-Z][A-Z0-9_]+-\d+")
TIMEOUT = 30


def parse_issue_link(link: str) -> tuple[str, str]:
    """Return (base_url, issue_key) from a Jira ticket link, or raise ValueError (FR-03).

    Accepts .../browse/QA-101 and board links carrying ?selectedIssue=QA-101.
    """
    parsed = urlparse(link.strip())
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("Enter a full Jira ticket link, for example https://your-domain.atlassian.net/browse/QA-101")
    match = re.search(r"/browse/(" + _KEY_RE.pattern + ")", parsed.path)
    if not match:
        selected = parse_qs(parsed.query).get("selectedIssue", [""])[0]
        match = _KEY_RE.fullmatch(selected)
        key = selected if match else None
    else:
        key = match.group(1)
    if not key:
        raise ValueError("No Jira issue key (like QA-101) found in that link.")
    return f"{parsed.scheme}://{parsed.netloc}", key


def adf_to_text(node) -> str:
    """Flatten an Atlassian Document Format tree (or plain string) to text, one block per line."""
    if node is None:
        return ""
    if isinstance(node, str):
        return node
    kind = node.get("type")
    if kind == "text":
        return node.get("text", "")
    if kind == "hardBreak":
        return "\n"
    inner = node.get("content", [])
    if kind in ("bulletList", "orderedList"):
        lines = []
        for i, item in enumerate(inner, 1):
            prefix = f"{i}. " if kind == "orderedList" else "- "
            lines.append(prefix + adf_to_text(item).strip())
        return "\n".join(lines) + "\n"
    text = "".join(adf_to_text(c) for c in inner)
    if kind in ("paragraph", "heading", "listItem", "tableRow", "codeBlock", "blockquote"):
        return text + "\n"
    if kind in ("tableCell", "tableHeader"):
        return text.strip() + " | "
    return text


def _text_adf(text: str) -> dict:
    return {"type": "paragraph", "content": [{"type": "text", "text": text}]}


def build_comment_adf(status: str, pass_pct: float, ac_rows: list[dict]) -> dict:
    """Jira comment per the spec's rules. status is Pass / Partial / Fail.

    ac_rows: [{"id": "AC-1", "text": "...", "tests_run": 2, "passed": True | False | None (not run)}, ...]
    """
    if status == "Pass":
        content = [_text_adf("ACCEPTANCE CRITERIA FULFILLED. PASSED.")]
    elif status == "Fail":
        content = [_text_adf("ACCEPTANCE CRITERIA NOT MET. FAILED.")]
    elif status == "Partial":
        header = [{"type": "tableHeader", "attrs": {}, "content": [_text_adf(h)]}
                  for h in ("Acceptance criterion", "Tests run", "Result")]
        rows = [{"type": "tableRow", "content": header}]
        for r in ac_rows:
            result = "Not run" if r["passed"] is None else "Passed" if r["passed"] else "Failed"
            cells = [f"{r['id']}: {r['text']}", str(r["tests_run"]), result]
            rows.append({"type": "tableRow", "content": [
                {"type": "tableCell", "attrs": {}, "content": [_text_adf(c)]} for c in cells]})
        content = [
            _text_adf(f"ACCEPTANCE CRITERIA PARTIALLY MET. ({pass_pct:.0f}%)"),
            {"type": "table", "attrs": {"isNumberColumnEnabled": False, "layout": "default"},
             "content": rows},
        ]
    else:
        raise ValueError(f"Unknown status: {status}")
    return {"version": 1, "type": "doc", "content": content}


class JiraClient:
    def __init__(self, base_url: str, email: str, api_token: str, session: requests.Session | None = None):
        if not (base_url and email and api_token):
            raise ServiceError("Jira is not configured. Set JIRA_BASE_URL, JIRA_EMAIL and JIRA_API_TOKEN in .env.")
        self.base_url = base_url.rstrip("/")
        self._session = session or requests.Session()
        self._session.auth = (email, api_token)

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        url = f"{self.base_url}/rest/api/3{path}"
        try:
            resp = self._session.request(method, url, timeout=TIMEOUT, **kwargs)
        except requests.RequestException as exc:
            raise ServiceError(f"Could not reach Jira: {exc}") from exc
        if resp.status_code in (401, 403):
            raise ServiceError("Jira rejected the credentials or permissions (check JIRA_EMAIL / JIRA_API_TOKEN).")
        if resp.status_code == 404:
            # Atlassian also answers 404 for a wrong token or site, so name all three causes.
            raise ServiceError("Jira ticket not found. Check the ticket key, that you can open it, "
                               "and JIRA_BASE_URL / JIRA_EMAIL / JIRA_API_TOKEN in .env.")
        if not resp.ok:
            raise ServiceError(f"Jira returned an error ({resp.status_code}): {resp.text[:200]}")
        return resp

    def get_issue(self, key: str) -> dict:
        """Return {key, summary, description, acceptance_field}. Text is flattened from ADF."""
        data = self._request("GET", f"/issue/{key}", params={"expand": "names"}).json()
        fields = data.get("fields", {})
        ac_text = ""
        for field_id, name in data.get("names", {}).items():
            if "acceptance criteria" in name.lower() and fields.get(field_id):
                ac_text = adf_to_text(fields[field_id]).strip()
                break
        return {
            "key": data.get("key", key),
            "summary": fields.get("summary", ""),
            "description": adf_to_text(fields.get("description")).strip(),
            "acceptance_field": ac_text,
        }

    def attach_file(self, key: str, path: Path | str) -> None:
        path = Path(path)
        with path.open("rb") as fh:
            self._request("POST", f"/issue/{key}/attachments",
                          headers={"X-Atlassian-Token": "no-check"}, files={"file": (path.name, fh)})

    def add_comment(self, key: str, adf_body: dict) -> None:
        self._request("POST", f"/issue/{key}/comment", json={"body": adf_body})
