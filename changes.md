# Changes from the specification

Differences between `QA Test Case Generator Agent - Specification.docx` and what was built, so the spec can be updated to match. Each item says what the spec said, what was built, and why. Nothing here is published to GitHub or Jira.

Status key: **Decided** = you chose it; **Assumed** = I picked a default for an open question or gap, please confirm.

---

## 1. Visual design (replaces the "Visual design" and "Readability rules" sections)

The two reference designs you supplied replace the original brown/teal and near-black/orange palettes. Colors were sampled from the image pixels.

### 1.1 Registration page: based on the "Signup UI Concept" reference (Decided)

| Role | Share | Color | Used for |
|---|---|---|---|
| Dominant | 60% | White `#FFFFFF`, panel `#FCFEFF` | Page and form panel |
| Secondary | 30% | Deep teal `#007074` (light `#419498`) | Register button, left block, rounded art panel |
| Accent | 10% | Yellow `#FDD25D` | Yellow block, circle outlines, HELLO WORLD message, focus ring |
| Text | n/a | Dark teal `#043133` (headings), gray `#454545` (labels, headline) | |
| Fields | n/a | `#EFF0F2` background, placeholder `#5F656B` | Inputs |

- Typography: **Poppins** (weights 400, 500, 600, 800), with Segoe UI and system fonts as fallback. The big headline is Poppins ExtraBold.
- Layout: three columns on wide screens (headline with yellow square and teal block, rounded teal panel with yellow circle outlines, form panel); stacked on screens under 1000px, with the art panel hidden. The reference photo is not used; the teal panel stands in for it.
- Added visible text: headline "JOIN US / CREATE YOUR ACCOUNT" and form heading "Welcome". Field placeholders added ("Enter your username", "Enter your password").
- Not added from the reference: Full Name, Email, "Log in" link, Google/GitHub sign-up buttons, "OR" divider. The spec only calls for username, password and Register.
- Error message color `#B3261E` (red, 6.5:1 on white) is outside the 3-color palette, kept for recognisability. It is shown with a warning icon.

### 1.2 Agentic QA app: based on the "WeHR dashboard" reference (Decided)

| Role | Share | Color | Used for |
|---|---|---|---|
| Dominant | 60% | Near-white `#FAFAFA`, white `#FFFFFF` cards | Page background, sidebar, cards |
| Secondary | 30% | Navy `#121843` | Text, headings, brand |
| Accent | 10% | Coral `#FF5151` | Primary buttons (Start a run, OK TO PUSH TO GIT), status banners, TEST COMPLETE, active nav marker |
| Tints | n/a | Peach `#FFE7DF`, blue `#E8F0FB`, pink `#FDEBF9` | Stat cards and decision chips |
| Muted text | n/a | `#5B607F` | Secondary text |

- Typography: **Playfair Display** (400 to 900), a serif, used across the whole app (you chose it after the first reference-based pick of Plus Jakarta Sans); Georgia fallback. Numbers use lining figures so digits sit at one height. The Gherkin code blocks stay monospace so their indentation lines up, and Material icons keep their own icon font.
- Look: light theme, white rounded cards with soft borders, pastel stat cards, left sidebar with brand and menu.
- The app is now **light**, where the spec said near-black.

### 1.3 Readability rules, updated contrast values

The spec's rule "white text on accent fails AA" still applies, now to the coral. Measured ratios:

| Pair | Ratio | Passes AA (4.5:1) |
|---|---|---|
| Navy on white | 17.0:1 | Yes |
| Navy on coral `#FF5151` | 5.3:1 | Yes |
| White on coral | 3.2:1 | **No**, so coral buttons and banners use navy text (the reference uses white) |
| Muted `#5B607F` on white | 6.1:1 | Yes |
| White on teal `#007074` | 5.9:1 | Yes |
| Dark teal on white / on yellow | 14.1:1 / 9.8:1 | Yes |
| Gray `#454545` on white | 9.6:1 | Yes |

- Pass/fail and approve/reject always show an icon plus the word (Passed, Failed, Approved, Rejected, Pending), never color alone. Unchanged from the spec.
- The spec's old rule of using gray `#8C8E92` for fills is dropped: white text on that gray is only about 3.2:1. Gray is no longer used for fills.

---

## 2. Registration page behavior (Spec section: AUT-1 to AUT-5, open question 5)

| Item | Spec | Built | Status |
|---|---|---|---|
| Validation rules | Open question | Username and password both required; password at least 8 characters | Assumed |
| Invalid input | Open question | Inline error in `data-testid="error"`: "Username is required.", "Password is required.", "Password must be at least 8 characters." | Assumed |
| Success | Shows HELLO WORLD | Shows HELLO WORLD in `data-testid="success"` | As spec |
| Test IDs | `data-testid="username"` as an example | `username`, `password`, `register`, `error`, `success`, `form`, `header` | Extended |
| URL | Fixed local URL | `http://localhost:8000`, started by `aut/serve.py`, or automatically by the agent app when tests run | As spec |

The Jira acceptance criteria must match these rules, since the agent only tests what the ticket says.

---

## 3. Agentic app: workflow and requirements

| Ref | Spec | Built | Status |
|---|---|---|---|
| FR-01 landing | Two buttons | Those two buttons, plus a sidebar (Dashboard, Start a run, Past runs), three stat cards (total runs, passed, needs attention) and a "Recent runs" list | Extended |
| FR-01 landing, chart | Not in spec | A **"Run results" donut chart** beside "Recent runs" shows the share of Pass, Partial and Fail runs, with the total in the middle. Runs with other statuses (Rejected, Pushed – not executed, in progress) are not charted. Colors Pass `#3B5BDB`, Partial `#9A7BE0`, Fail `#FF5151` (checked for color-blind separation and contrast); the legend also shows an icon, the word, the count and the percentage | Extended (Decided) |
| Ongoing runs (new) | Not in spec | A run stays "ongoing" from start until TEST COMPLETE. Leaving it (Back, sidebar, dashboard) no longer loses it: the sidebar has an **ONGOING RUNS** section with a button that reopens the run on the screen it was left on, the dashboard shows an "Ongoing run" card with **Resume run**, and the Start a run page warns that starting a new run replaces the ongoing one (it stays saved in Past runs). One ongoing run per browser session; it does not survive a page refresh or app restart | Extended (Decided) |
| Test execution in the background (new) | Not specified | **Run tests** now executes on a background thread and shows a progress page, so the run continues while you are on another page. A **spinner** shows under ONGOING RUNS (and on the dashboard card) while tests run, and changes to "Report ready" when they finish. If a run fails you get an error with **Retry** | Extended (Decided) |
| Stage card (new) | Spec only asks the app to show each agent step (NFR transparency) | The stages of a run ("Reading Jira", "Drafting test cases", "Checking the registration page", "Running 4 test case(s)") are shown in a **black card that only appears once the first stage exists and grows by one line per new stage**. Finished stages are gray-navy with a green tick, the current stage is navy with a spinner, and a failed stage is shown with a red cross | Decided |
| Sidebar sections | Not in spec | Sidebar sections are MAIN MENU (Dashboard, Start a run, Past runs) and ONGOING RUNS | Extended |
| Blue text (visual) | Not in spec | Blue text in the QA app (the Gherkin keywords Given, When, Then, Scenario, and ordinary links) uses blue `#0047AB` (8.4:1 on white). Blue fills such as the chart's Pass segment and the approved chip border are not text and are unchanged | Decided |
| Cards (visual) | Cards were gray/white | Cards on the main screens are **pastel**, not black: test case cards (tint follows the decision: lilac pending, blue approved, peach rejected), the dashboard's **Recent runs** (blue) and **Run results** (lilac) cards, **each run on the Past runs page** (tint follows the status: blue Pass, lilac Partial, pink Fail, peach others), the **Start a run form** (blue) and the **stage card** (lilac). Text on them is navy. Gherkin is shown on a white plate with darker syntax colors (tags `#C62F2F`, keywords blue `#0047AB`, quoted values `#176B43`), and the donut sits on a white plate so its colors keep their validated contrast. Decision chips are white with a colored border. The only black items left are the hovered and selected items in the left menu | Decided |
| Pastel text cards (visual) | Not in spec | Text that used to sit directly on the page background is now on light pastel cards with navy text: page titles and subtitles (light coral `#FFE3E3` cards (a light tint of `#FF5151`) with coral `#FF5151` heading text and navy sub-text, used for page headings only. Coral on this tint is about 2.65:1, below the 3:1 large-text minimum; navy heading text would be about 14:1| Decided |
| Translucent black cards (visual) | Not in spec | Every card that was pastel (pink, peach, blue, lilac), including the test case cards, Past runs rows, the dashboard cards, the Start a run form, the stage card and the cards in the left menu, is now **black at 70% transparency** (`rgba(0,0,0,0.3)`), which shows as a mid grey over the light page. Text on them is navy `#121843` (about 7.7:1) because white text on that grey would be only about 2.4:1. The page-heading coral-tint cards, the white plates for Gherkin and the chart, and the solid black stat cards are unchanged. Cards are no longer tinted by status or decision, since they now share one color; the chips and words still show the status | Decided |
| Dashboard stat cards (visual) | Not in spec | The **Total runs**, **Passed** and **Needs attention** cards are black (`#0A0A0A`) with white labels, coral `#FF5151` numbers (5.3:1) and light gray notes | Decided |
| Sidebar text size (visual) | Not in spec | "No ongoing runs" and the running-tests line in the left menu use the same 14px size as Dashboard, Start a run and Past runs | Decided |
| Sidebar cards (visual) | Not in spec | The left menu uses the same look: the QA Agent brand on a light coral `#FFE3E3` card with coral text (the same scheme as the page headings, left aligned), MAIN MENU on a blue card, ONGOING RUNS on a peach card. Hovered and selected items stay black with white text | Decided |
| Sidebar hover and selected item | Not in spec | Hovered, keyboard-focused and selected sidebar items are **black with white text** (the selected item also keeps a coral edge marker) | Decided |
| Dashboard alignment | Not in spec | The dashboard heading, subheading, and **Start a run** and **View past runs** buttons are center-aligned | Decided |
| Start a run and Past runs alignment | Not in spec | On the **Start a run** page everything is centered in a narrower column (heading, ticket link label, text box, Start and Back). On the **Past runs** list the heading, Back button, column headers, every cell and the Open buttons are centered. The ticket link text box inside the black card is a light field with navy text (white background) so it stands out on black | Decided |
| FR-03 link check | Check the link is valid | Also rejects a link whose host differs from the configured `JIRA_BASE_URL` | Extended |
| FR-04/05 | Extract and number criteria | Done by Claude; if no criteria are found the run stops with a message to fix the ticket | As spec, plus guard |
| FR-06 to FR-08 | Draft all test cases, tag them, check coverage | Gherkin limited to a **fixed step vocabulary** (11 step shapes) so every scenario is executable. Invalid scenarios get one repair attempt, then are dropped with a warning. Uncovered criteria get up to 2 follow-up drafts. Any still uncovered are shown as a warning | New constraint |
| FR-09 Approve all | Per-case Approve, Edit, Reject only | An **"Approve all test cases" checkbox** above the list approves every case at once (including any rejected ones). It is ticked automatically when every case is approved, and unticking it returns all cases to Pending. Approving or rejecting a single case still works and updates the box | Extended (Decided) |
| FR-09 Edit | Opens the Gherkin text | Edited text is validated (one scenario, one `@AC-n`, one type tag, allowed steps); a saved edit returns the case to **Pending**, so it must be approved again | Assumed |
| FR-10 | Push enabled after all approved or rejected | Also requires at least one approved case | Assumed (open question 2) |
| Open question 2 | All rejected | Push disabled and a **Regenerate test cases** button is offered | Decided (spec's own proposal) |
| FR-11 | Push approved cases as `.feature` | Pushed to `tests/features/<KEY>.feature`; commit message "Add test cases for <KEY>"; re-pushing the same key updates the file | As spec |
| FR-12 | Ask to execute, Yes / No | As spec | As spec |
| Open question 1 | No to execute | Run saved with status **"Pushed – not executed"** and TEST COMPLETE shown | Decided (spec's own proposal) |
| FR-13 | All or selected | Radio (All / Selected) with a checkbox per approved case | As spec |
| FR-14 | Run and record pass/fail with reason | Run in a real Chromium browser through pytest-bdd and Playwright; failure reason is taken from the assertion message | As spec |
| FR-16 | Per-criterion result | Adds **"Not run"** for criteria whose tests were not selected; a criterion passes only if every test tagged with it passed | Extended |
| FR-17 to FR-19 | Attach report and comment, or discard | As spec. Retrying after a failure never attaches the report twice | As spec |
| FR-21 history | Save every run | Run is saved from the moment it starts, so interrupted runs also appear. Statuses: Started, Drafted, Pushed, Executed, Pass, Partial, Fail, Rejected, Pushed – not executed | Extended |
| NFR reliability | Clear error and retry | Each failing step shows a message and a retry. Jira's 404 message names all three likely causes (wrong key, no access, wrong credentials), because Atlassian also returns 404 for a bad token or site | As spec |

---

## 4. GitHub repository contents (Decided)

The spec only said feature files are pushed. You decided the repo holds **only three things**:

| # | Content | Path in repo |
|---|---|---|
| 1 | Registration application | `aut/` |
| 2 | Execution test cases | `tests/features/<KEY>.feature`, plus step definitions `tests/steps/`, `tests/conftest.py`, `tests/test_features.py` so the repo can run on its own (Assumed) |
| 3 | Execution test report | `reports/<KEY>-...html` |

- **New write beyond the spec:** the report is also committed to GitHub, at the same moment it is attached to Jira (the **Yes** answer). **Discard** commits nothing. This is an extra GitHub write that the spec did not have; it is still behind a button click.
- The agent app, its tests, scripts, prompts, `.env` and run history stay local and are never pushed.
- The registration app and step definitions are published once by `scripts/publish_repo_assets.py` (dry run by default). **Not yet published**, at your request.

---

## 5. Report (open questions 3 and 4)

| Item | Spec | Built | Status |
|---|---|---|---|
| Title | `Execution Report : [JIRA]-[Date]-[Time]` | `Execution Report : SCRUM-5-2026-11-14-20:26` (24-hour local time, `YYYY-MM-DD-HH:mm`) | Assumed (open question 3) |
| File name | Not stated | Colons are not allowed in Windows file names, so the file uses `-`: `Execution Report - SCRUM-5-2026-11-14-20-26.html`. In the repo, spaces become underscores | Assumed |
| Format | HTML or PDF | **HTML**, self-contained | Assumed (open question 4) |
| Contents | Overall status, pass %, per-test, per-criterion | As spec, plus failure reasons and a "Not run" state | As spec |

## 6. Jira comment (spec "Jira comment rules")

| Status | Spec | Built |
|---|---|---|
| Pass | `ACCEPTANCE CRITERIA FULFILLED. PASSED.` | As spec |
| Fail | `ACCEPTANCE CRITERIA NOT MET. FAILED.` | As spec |
| Partial | Text plus a criteria table | Same, built as a Jira table (rich text format). Rows for criteria that were not run show "Not run" |

---

## 7. Tech stack (spec "Proposed tech stack", described as swappable)

| Component | Spec proposal | Built | Note |
|---|---|---|---|
| LLM | Claude or OpenAI | **Claude Sonnet 5.5** (`claude-sonnet-5-5`) | Decided. This model rejects forced tool choice, so structured answers use `tool_choice: auto` plus an instruction to call the tool |
| Everything else | Streamlit, Jira REST, PyGithub, pytest-bdd + Playwright, SQLite | As proposed | |
| Python | Not stated | 3.12, installed with winget | |
| Virtualenv | Not stated | `%LOCALAPPDATA%\qa-agent-venv`, **outside** the project: the project path is too long for numpy on Windows, and OneDrive would sync it | |
| Run history | "Local JSON or SQLite" | SQLite `data/runs.db`; reports in `data/reports/` | |
| Fonts | Not stated | Loaded from Google Fonts at view time; offline, the fallback font is used. Bundling the font files locally would need a download, so it was not done | Assumed |
| First page load | Not stated | About 20 seconds on a cold start while Python imports warm up | |

## 8. Extras not in the spec

- **Demo mode:** `scripts/demo_app.py` runs the real UI on fake Jira, GitHub and Claude, with sample past runs, so the demo can be rehearsed with no credentials.
- **Real-service checks:** `scripts/smoke_services.py` (read-only), `scripts/smoke_writes.py` (writes then cleans up) and `scripts/e2e_real.py` (full run, needs `--confirm-writes`).
- **Auto-start of the registration page:** the agent app starts the page on port 8000 if nothing is answering when tests run.
- **Test suite:** unit, workflow, UI and browser integration tests, including deliberately broken copies of the registration page to prove Partial and Fail results.

## 9. Spec items that remain open or unchanged

- Everything in "Scope", "Success criteria", FR-02, FR-15, FR-20 and the demo plan behaves as written.
- The demo plan's "edit one, reject one" step works as written; note an edited case returns to Pending and must be approved again.
- Multi-user access, real accounts, a database for the registration page and security hardening remain out of scope.
