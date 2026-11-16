# QA Test Case Generator Agent: Implementation Plan

Source: `QA Test Case Generator Agent - Specification.docx` (21 FRs, 5 AUT reqs, 5 NFRs). Everything runs locally on Windows 10.

## 1. Tech stack (local, single-user, one Python codebase)

| Component | Choice | Why it fits a local build |
|---|---|---|
| Language / env | Python 3.11+, `venv`, `requirements.txt` | One language for UI, agent, runner. |
| AUT (registration page) | Plain HTML/CSS/JS, served by `python -m http.server 8000` (started by the app) | Zero build step; fixed URL `http://localhost:8000` (AUT-5). |
| Agentic app UI | **Streamlit**, `st.session_state` as the run state machine | Matches the spec; gating screens (approve/edit/reject, Yes/No) map to buttons. Theme via `.streamlit/config.toml` + small CSS injection for the 60-30-10 palette. |
| LLM | **Anthropic Claude API** (`anthropic` SDK), tool-use / JSON output for structured results | Needs structured output (criteria list, scenarios with tags). Model name kept in `.env`. |
| Jira | Jira Cloud REST v3 via `requests` (Basic auth: email + API token) | `GET /issue/{key}`, `POST /issue/{key}/attachments` (needs `X-Atlassian-Token: no-check`), `POST /issue/{key}/comment` (ADF body). |
| GitHub | `PyGithub` | Create/update `tests/features/<KEY>.feature`, return commit URL. |
| Test execution | `pytest-bdd` + `playwright` (Chromium), run as a **subprocess** | Subprocess avoids Playwright-sync vs Streamlit event-loop conflicts, and gives clean per-scenario results. |
| Report | Jinja2 -> self-contained HTML (decision: HTML, see Open Questions) | Easy to attach to Jira; no PDF toolchain on Windows. |
| History | **SQLite** (stdlib `sqlite3`), `data/runs.db` | One file, queryable for the past-runs table; JSON blobs for test cases/results. |
| Config / secrets | `.env` via `python-dotenv`, `.env` in `.gitignore`, `.env.example` committed | NFR: tokens never in code/repo. |
| Dev tooling | `pytest` (unit tests with mocked Jira/GitHub/LLM), `ruff` | Verifies the agent without hitting real services. |

Alternative considered and rejected: FastAPI + React. More flexible UI but doubles the work for one person; Streamlit satisfies every UI requirement.

## 2. Project layout

```
Individual_Project_Build/
  aut/                      index.html, style.css, app.js        (AUT-1..5)
  agent_app/
    app.py                  Streamlit entry, screen router
    state.py                Run dataclass + step enum
    ui/                     landing.py, start_run.py, review.py, execute.py, history.py, theme.py
    services/
      jira_client.py        parse key from URL, fetch issue, ADF->text, attach, comment
      github_client.py      push_feature()
      llm.py                extract_criteria(), generate_gherkin(), check_coverage(), write_comment()
      runner.py             write temp feature dir, run pytest-bdd, parse results
      report.py             build HTML report
      store.py              SQLite CRUD
    prompts/                *.md prompt templates
  tests_runtime/            step definitions (conftest.py, steps/registration_steps.py)
  tests/                    unit tests for the app itself
  data/                     runs.db, reports/        (gitignored)
  .env.example  requirements.txt  README.md  .streamlit/config.toml
```

## 2a. What lives in the GitHub repo (decided)

The GitHub repo holds **only** three things. The agentic QA app (`agent_app/`), its tests, scripts, prompts, `.env` and run history stay local and are never pushed.

| # | Content | Repo path | Written by |
|---|---|---|---|
| 1 | Registration application (AUT) | `aut/` (`index.html`, `style.css`, `app.js`, `serve.py`) | One-time push from this project |
| 2 | Execution test cases | `tests/features/<KEY>.feature`, plus the step definitions needed to run them (`tests/steps/`, `tests/conftest.py`) *(assumption, see below)* | Agent, on OK TO PUSH TO GIT (feature files); one-time push (step definitions) |
| 3 | Execution test report | `reports/<KEY>-<date>-<time>.html` *(assumption, see below)* | Agent, only after the user approves the report |

Assumptions to confirm:
- **Step definitions** ship with the test cases, since a `.feature` file cannot run without them. The `tests_runtime/` folder here is the source; it is pushed as `tests/steps/` so the repo is self-contained.
- **The report is committed to the repo** (in addition to being attached to Jira). This adds a GitHub write beyond the spec's FR-11, so it follows the same rule: no write without a button click. It is committed when the user answers Yes to "attach this report in Jira"; Discard commits nothing.

Consequences for the build: `github_client` gets a general `push_file(path, content, message)` (the feature push becomes a thin wrapper over it); Phase 5's Yes path commits the report; the run history stores the report's commit link alongside the feature file's.

## 3. Key design decisions

1. **Run state machine** (persisted to SQLite at every transition so discarded and aborted runs also appear in history, FR-21):
   `URL_ENTERED -> JIRA_READ -> DRAFTED -> REVIEWED -> PUSHED -> (EXECUTED -> REPORTED -> ATTACHED | REJECTED) | PUSHED_NOT_EXECUTED`.
2. **Human gates enforced in code, not just UI**: `github_client.push_feature` and `jira_client.attach/comment` are only reachable from button callbacks, which check the state; no agent code path calls them directly.
3. **Traceability**: LLM must return scenarios as structured objects `{ac_id, type, title, steps}`. The app renders the Gherkin and the `@AC-n @type` tags itself, so tags can't be malformed. Coverage check (FR-08) is a deterministic set difference (ACs without a scenario), looping the LLM for missing ones (max 2 retries).
4. **Executing Gherkin without hand-written steps per generated scenario**: this is the main technical risk. Approach: constrain the LLM to a **fixed step vocabulary** that the AUT supports (e.g. `Given I am on the registration page`, `When I enter username "<x>" and password "<y>"`, `And I click Register`, `Then I should see "<text>"`, `Then I should not see "<text>"`, `Then the password field should be masked`, ...). Step defs in `tests_runtime/` implement exactly that vocabulary with Playwright using `data-testid` selectors. Generation prompt includes the vocabulary; a validator rejects/regenerates scenarios with unknown steps. (Fallback: mark unknown-step scenarios as "Not executable" instead of failing silently.)
5. **Results parsing**: run `pytest --json-report` (or JUnit XML); map each scenario to its tags via pytest-bdd markers; failure reason = assertion message.
6. **Status math**: pass % = passed / run x 100; Pass = 100, Fail = 0, else Partial. AC passes only if all its executed tests pass; ACs with no selected tests show "Not run".
7. **Transparency (NFR)**: `st.status` blocks with step labels ("Reading Jira", "Drafting test cases", ...).
8. **Reliability (NFR)**: each service call wrapped; on failure show the error plus a Retry button that re-runs that step only.
9. **Report name**: title `Execution Report : QA-101-2026-11-14-18:30`; the file on disk uses `-` instead of `:` because Windows forbids colons in filenames.
10. **Jira ADF**: description comes back as Atlassian Document Format; flatten to text, then LLM extracts acceptance criteria (also check a custom "Acceptance Criteria" field if present). Jira comment is built as ADF, including a table for the Partial case.

## 4. Phases

**Phase 0: Setup (0.5 day).** venv, dependencies, `playwright install chromium`, `.env.example`, Streamlit theme. Create/confirm a Jira Cloud project + API token, a GitHub repo + PAT (fine-grained, Contents: write). *Done when:* `streamlit run` shows a blank themed page.

**Phase 1: AUT (0.5 day).** Page with username, password (type=password), Register button; `data-testid` on every element incl. result message; on valid input show `HELLO WORLD`; colors per palette (#6B4A33 / #C9CCD0 / #00C2B8, dark text #19191B on teal). Validation rules: see Open Questions (propose: both fields required, password min 8 chars, inline error with `data-testid="error"`). Launcher script serves it on port 8000. *Done when:* manual check of AUT-1..5.

**Phase 2: Services with mocks (1.5 days).** `jira_client`, `github_client`, `llm`, `store`, each with unit tests against mocked HTTP/SDK. Smoke-test real Jira (read ticket) and real GitHub (push a file) from a script. *Done when:* real ticket yields numbered ACs; real push returns commit URL.

**Phase 3: Generation + coverage (1 day).** Prompts, step-vocabulary validation, tagging, coverage loop. Evaluate on 2-3 hand-written Jira tickets. *Done when:* every AC has >=1 scenario and all steps are in the vocabulary.

**Phase 4: Runner + report (1.5 days).** Step definitions, subprocess runner, result parser, HTML report, status/AC rollup. Run against the AUT with a hand-written feature, including a deliberately broken AUT variant to prove Fail/Partial. *Done when:* a 15-scenario run finishes under 5 minutes and report shows per-test and per-AC results.

**Phase 5: Streamlit workflow (2 days).** Landing (FR-01), Start run + URL validation (FR-03), Read Jira/AC list (FR-04/05), Review screen with Approve/Edit/Reject and gated OK TO PUSH TO GIT (FR-09/10), push + success prompt (FR-11/12), execute selection with checkboxes (FR-13/14), report view (FR-15/16), Jira Yes/Discard (FR-17..19), TEST COMPLETE (FR-20), history list + detail (FR-02/21). Apply agent-app palette and accessibility rules (icon + word for Passed/Failed). *Done when:* full path works end to end with mocks.

**Phase 6: Integration, hardening, demo (1 day).** Real end-to-end run with Jira + GitHub, error/retry paths (kill network, bad token), README, demo rehearsal following the spec's 5-minute plan.

Estimated total: about 8 working days.

## 5. Requirement traceability

| Requirements | Phase / module |
|---|---|
| AUT-1..5 | Phase 1, `aut/` |
| FR-01, 02, 21 | Phase 5, `ui/landing.py`, `ui/history.py`, `store.py` |
| FR-03..05 | `ui/start_run.py`, `jira_client.py`, `llm.extract_criteria` |
| FR-06..08 | `llm.generate_gherkin`, coverage loop |
| FR-09, 10 | `ui/review.py` |
| FR-11, 12 | `github_client.py`, `ui/review.py` |
| FR-13..16 | `ui/execute.py`, `runner.py`, `report.py` |
| FR-17..20 | `jira_client.py`, `llm.write_comment`, `ui/execute.py` |
| NFR human-in-loop / security / reliability / transparency / performance | state guards, `.env`, retry wrappers, `st.status`, Phase 4 timing check |

## 6. Open questions with proposed defaults (spec leaves these open)

1. **User answers No to execute:** end run, status `Pushed – not executed`, show TEST COMPLETE (spec's proposal).
2. **All test cases rejected:** disable push, offer Regenerate (spec's proposal).
3. **Report name format:** `YYYY-MM-DD-HH:mm` as in the spec example (24h, local time); filename uses `-` for the colon.
4. **Report attachment format:** HTML (no extra dependencies; PDF can be added later via Playwright `page.pdf()`, which is already installed).
5. **AUT validation rules:** username and password required; password >= 8 characters; show `data-testid="error"` message otherwise. This gives the agent real negative and boundary cases to test. Confirm with the instructor/Jira ticket author, since the Jira ACs must match.

## 7. Risks

| Risk | Mitigation |
|---|---|
| LLM generates steps with no implementation | Fixed step vocabulary + validator (design decision 4). |
| Streamlit reruns lose state mid-run | All state in `st.session_state`, mirrored to SQLite per transition. |
| Jira ADF parsing and attachment quirks | Build small ADF helper; test against the real instance early (Phase 2). |
| Tokens leaked into repo | `.gitignore` + `.env.example`; no secrets in logs or run history. |
| Playwright first-run download / Windows paths | Documented in README; run pytest with `sys.executable -m pytest` and absolute paths. |
| LLM output variance breaks demo | Low temperature, schema-validated output, a pre-tested demo ticket, run history from a rehearsal as backup. |
