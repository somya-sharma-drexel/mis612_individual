"""Agentic app look, sampled from the WeHR dashboard reference.

Palette (60-30-10): near-white #FAFAFA and white cards (60%), navy #121843 (30%: text, headings),
coral #FF5151 (10%: primary buttons, status banners). Cards are black at 70% transparency (stat cards are solid black). Typeface: Playfair Display (serif) with Georgia fallbacks; Gherkin code stays monospace.

Contrast: navy on white 17.0:1, navy on coral 5.3:1 (white on coral is only 3.2:1, so coral never
carries white text), muted #5B607F on white 6.1:1.
"""
import html
import re

import streamlit as st

from agent_app.ui.ongoing import SPINNER, render_ongoing

NAV = {"home": "Dashboard", "start": "Start a run", "history": "Past runs"}
NAV_OF_SCREEN = {"landing": "home", "history": "history", "history_detail": "history"}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700;800;900&display=swap');

/* Playfair Display everywhere (serif fallbacks if the web font cannot load). Material icons keep their own icon font. */
html, body, .stApp, .stApp *:not([data-testid="stIconMaterial"]), [data-testid="stSidebar"], [data-testid="stSidebar"] *:not([data-testid="stIconMaterial"]) {
    font-family: 'Playfair Display', Georgia, 'Times New Roman', serif; font-variant-numeric: lining-nums; }  /* even-height digits */
a { color: #0047AB; }  /* blue for ordinary links; links on cards stay navy (.pcard a) */
h1, h2, h3 { color: #121843; font-weight: 800; letter-spacing: -0.01em; }
.block-container { padding-top: 2.5rem; max-width: 1180px; }

/* Buttons: coral primary with navy text; white secondary with a soft border */
.stButton > button, .stDownloadButton > button {
    border-radius: 10px; border: 1px solid #E3E5EE; background: #FFFFFF; color: #121843; font-weight: 600;
}
.stButton > button:hover, .stDownloadButton > button:hover { border-color: #FF5151; color: #121843; }
.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {
    background: #FF5151; border-color: #FF5151; color: #121843; font-weight: 700;
}
.stButton > button[kind="primary"] p, .stDownloadButton > button[kind="primary"] p { color: #121843; }
.stButton > button[kind="primary"]:hover { background: #FF6767; border-color: #FF6767; }
.stButton > button:disabled { opacity: 0.45; }

/* Cards: white, rounded, soft border */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #FFFFFF; border: 1px solid #E8EAF0; border-radius: 14px;
}
div[data-testid="stExpander"] details { background: #FFFFFF; border: 1px solid #E8EAF0; border-radius: 14px; }
div[data-baseweb="input"], div[data-baseweb="textarea"] { border-radius: 10px; }
div[data-testid="stCode"] pre { background: #F6F7FB; border-radius: 10px; }
table { border-collapse: collapse; }
thead th { background: #F6F7FB; color: #121843; }

/* Sidebar */
[data-testid="stSidebar"] { border-right: 1px solid #E8EAF0; }
.brand { display: flex; align-items: center; gap: 10px; font-size: 1.35rem; font-weight: 800; color: #121843; }
.brand-mark { background: #FF5151; color: #121843; border-radius: 10px; padding: 4px 8px; font-size: 1rem; font-weight: 800; }
.nav-label { color: #121843; font-size: 0.72rem; font-weight: 700; letter-spacing: 0.08em; margin: 0 0 6px 4px; }
/* Sidebar cards: brand on pink, main menu on blue, ongoing runs on peach (navy text on each) */
.brand-card { padding: 12px 14px; margin: 4px 0 12px; }
[data-testid="stSidebar"] [class*="st-key-pcard_"] { padding: 12px 10px; }
[data-testid="stSidebar"] [class*="st-key-pcard_"] .muted { color: #121843; }
/* "No ongoing runs" uses the same size as the menu buttons (Dashboard, Start a run, Past runs: 14px) */
[data-testid="stSidebar"] .muted, [data-testid="stSidebar"] .ongoing-row { font-size: 14px; font-weight: 400; }
[data-testid="stSidebar"] [class*="st-key-pcard_"] .stButton > button { color: #121843; }
[data-testid="stSidebar"] .stButton > button { border: 0; background: transparent; justify-content: flex-start;
    font-weight: 600; color: #5B607F; border-radius: 10px; }
[data-testid="stSidebar"] .stButton > button > div,
[data-testid="stSidebar"] .stButton > button > div > span { justify-content: flex-start; width: 100%; text-align: left; }
[data-testid="stSidebar"] .stButton > button p { text-align: left; }
/* Hover and keyboard focus: black with white text (white on #0A0A0A is 19.5:1) */
[data-testid="stSidebar"] .stButton > button:hover, [data-testid="stSidebar"] .stButton > button:focus-visible {
    background: #0A0A0A; color: #FFFFFF; }
[data-testid="stSidebar"] .stButton > button:hover p, [data-testid="stSidebar"] .stButton > button:focus-visible p {
    color: #FFFFFF; }

.st-key-hero, .st-key-hero h1, .st-key-hero p { text-align: center; }

/* Past runs page: everything centered (headings, table header, cell text, buttons) */
.st-key-history_page { width: 100%; max-width: 980px; margin-left: auto; margin-right: auto; text-align: center; }
.st-key-history_page h2, .st-key-history_page p { text-align: center; }
.st-key-history_page [data-testid="stColumn"] { text-align: center; }
.st-key-history_page [data-testid="stColumn"] > div, .st-key-history_page [data-testid="stColumn"] .stButton {
    display: flex; justify-content: center; }
.st-key-history_page [data-testid="stColumn"] [data-testid="stMarkdownContainer"] { width: 100%; }

/* Start a run page: everything centered in a narrower column */
.st-key-start_page { width: 100%; max-width: 720px; margin-left: auto; margin-right: auto; text-align: center; }
.st-key-start_page h2, .st-key-start_page p { text-align: center; }
.st-key-start_page [data-testid="stWidgetLabel"] { justify-content: center; width: 100%; }
.st-key-start_page [data-testid="stWidgetLabel"] p { text-align: center; }
.st-key-start_page input { text-align: center; }

/* Stage card: black at 70% transparency, grows as each new stage is added (navy text 7.9:1) */
.stage-card { background: rgba(0, 0, 0, 0.3); color: #121843; border-radius: 14px; padding: 16px 20px; margin: 12px 0;
              display: flex; flex-direction: column; gap: 10px; }
.stage { display: flex; align-items: center; gap: 10px; font-weight: 600; }
.stage-done { color: #121843; font-weight: 500; }
.stage-failed { color: #701313; }
.stage-tick { color: #0B3D24; }
.stage-card .spinner { border-color: rgba(18, 24, 67, 0.25); border-top-color: #FF5151; }

/* Cards for page text: light coral #FFE3E3 for page headings (coral #FF5151 heading text); every other card (formerly pink, peach,
   blue, lilac) is black at 70% transparency (rgba 0,0,0,0.3 = about #AFAFAF over the page) with navy #121843 text, 7.7:1. */
.pcard { border-radius: 14px; padding: 16px 22px; margin: 6px 0; color: #121843; }
.pcard-pink { background: rgba(0, 0, 0, 0.3); } .pcard-peach { background: rgba(0, 0, 0, 0.3); }
.pcard-blue { background: rgba(0, 0, 0, 0.3); } .pcard-lilac { background: rgba(0, 0, 0, 0.3); }
.pcard-grey { background: #FFE3E3; }  /* page headings only: light tint of the coral #FF5151 */
.pcard h1, .pcard h2, .pcard h3 { margin: 0; padding: 0; color: #121843; font-weight: 800;
                                  letter-spacing: -0.01em; line-height: 1.25; }
.pcard h1 { font-size: 2.2rem; } .pcard h2 { font-size: 1.75rem; } .pcard h3 { font-size: 1.3rem; }
.pcard p { margin: 6px 0 0; color: #121843; font-size: 0.95rem; }
.pcard a { color: #121843; font-weight: 700; }
/* Page headings: centered; heading text coral #FF5151 on #FFE3E3 is about 2.65:1 (below the 3:1 large-text minimum) */
.pcard-grey, .pcard-grey h1, .pcard-grey h2, .pcard-grey h3, .pcard-grey p { text-align: center; }
.pcard-grey h1, .pcard-grey h2, .pcard-grey h3 { color: #FF5151; }
.pcard-grey.brand { color: #FF5151; justify-content: flex-start; text-align: left; }  /* sidebar brand: same scheme as page headings, left aligned */
[class*="st-key-pcard_"] { border-radius: 14px; padding: 14px 20px; }
[class*="st-key-pcard_pink_"] { background: rgba(0, 0, 0, 0.3); } [class*="st-key-pcard_peach_"] { background: rgba(0, 0, 0, 0.3); }
[class*="st-key-pcard_blue_"] { background: rgba(0, 0, 0, 0.3); } [class*="st-key-pcard_lilac_"] { background: rgba(0, 0, 0, 0.3); }
[class*="st-key-pcard_grey_"] { background: #FFE3E3; }
[class*="st-key-pcard_"] h2, [class*="st-key-pcard_"] h3 { margin-top: 0; padding-top: 0; }

/* Status banner: coral with navy text */
.banner { background: #FF5151; color: #121843; font-weight: 800; font-size: 1.35rem;
          padding: 14px 20px; border-radius: 14px; margin: 12px 0; }

/* Stat cards (Total runs, Passed, Needs attention): black; labels white (19.5:1), numbers coral #FF5151 (5.3:1),
   notes #B4B8CC (10:1) */
.stat { border-radius: 14px; padding: 18px 20px; color: #FFFFFF; height: 100%; background: #0A0A0A; }
.stat-label { font-weight: 700; font-size: 0.95rem; color: #FFFFFF; }
.stat-value { font-weight: 800; font-size: 2.4rem; line-height: 1.2; color: #FF5151; }
.stat-note { font-size: 0.8rem; color: #B4B8CC; }

/* Decision chips (always icon + word, never color alone) */
.chip { display: inline-block; border-radius: 999px; padding: 2px 12px; font-size: 0.8rem; font-weight: 700; color: #121843;
        background: #FFFFFF; border: 1.5px solid #8A8FB0; }
.chip-approved { border-color: #3B5BDB; } .chip-rejected { border-color: #FF5151; } .chip-pending { border-color: #8A8FB0; }
.muted { color: #5B607F; }

/* Ongoing-run spinner (sidebar) */
.spinner { display: inline-block; width: 14px; height: 14px; border: 2px solid #E3E5EE; border-top-color: #FF5151;
           border-radius: 50%; animation: spin 0.8s linear infinite; flex: none; }
@keyframes spin { to { transform: rotate(360deg); } }
@media (prefers-reduced-motion: reduce) { .spinner { animation-duration: 3s; } }
.ongoing-row { display: flex; align-items: center; gap: 8px; padding: 4px 12px; font-size: 0.85rem;
               font-weight: 600; color: #121843; }

/* Inputs inside pastel panels: white field with a soft border and navy text */
[class*="st-key-pcard_"] div[data-baseweb="input"], [class*="st-key-pcard_"] div[data-baseweb="textarea"] {
    background: #FFFFFF; border: 1px solid #CFD3E6; border-radius: 10px; }
[class*="st-key-pcard_"] input::placeholder, [class*="st-key-pcard_"] textarea::placeholder { color: #5B607F; opacity: 1; }
[class*="st-key-pcard_"] input:focus, [class*="st-key-pcard_"] textarea:focus { border-color: #FF5151; }
[class*="st-key-pcard_"] .muted { color: #121843; }

/* Gherkin on a white plate inside a pastel card: text navy 17:1, tags #C62F2F 5.5:1,
   keywords blue #0047AB 8.4:1, quoted values #176B43 5.8:1 */
pre.gherkin { background: #FFFFFF; border: 1px solid #D9DCEA; border-radius: 10px; padding: 14px; margin: 8px 0;
              color: #121843; font-size: 0.85rem; overflow-x: auto; }
pre.gherkin, pre.gherkin * { font-family: Consolas, 'Courier New', monospace !important; }  /* keeps indentation aligned */
.g-tag { color: #C62F2F; } .g-kw { color: #0047AB; font-weight: 700; } .g-str { color: #176B43; }

/* Run-status donut on a white plate (the chart colors were validated on white) */
.donut-wrap { display: flex; align-items: center; gap: 24px; flex-wrap: wrap; padding: 14px 18px;
              background: #FFFFFF; border-radius: 12px; }
.legend { display: flex; flex-direction: column; gap: 10px; min-width: 150px; }
.legend-row { display: flex; align-items: center; gap: 8px; font-size: 0.9rem; }
.legend-dot { width: 12px; height: 12px; border-radius: 50%; flex: none; }
.legend-name { color: #121843; font-weight: 600; }
.legend-val { margin-left: auto; color: #121843; font-weight: 700; }
.donut-total { font-size: 22px; font-weight: 800; fill: #121843; }
.donut-sub { font-size: 9px; fill: #454B73; }
</style>
"""


def apply_theme(screen: str = "landing") -> None:
    """Inject the CSS and highlight the sidebar item for the current screen."""
    active = NAV_OF_SCREEN.get(screen, "start")
    st.markdown(CSS + f"""<style>
    .st-key-nav_{active} button {{ background: #0A0A0A !important; color: #FFFFFF !important;
        border-left: 4px solid #FF5151 !important; border-radius: 4px 10px 10px 4px !important; }}
    .st-key-nav_{active} button p {{ color: #FFFFFF !important; }}
    </style>""", unsafe_allow_html=True)


def render_sidebar() -> None:
    with st.sidebar:
        st.html('<div class="pcard pcard-grey brand brand-card"><span class="brand-mark">QA</span>QA Agent</div>')
        with panel("blue", "menu"):
            st.markdown('<div class="nav-label">MAIN MENU</div>', unsafe_allow_html=True)
            st.button(NAV["home"], key="nav_home", on_click=go, args=("landing",), width="stretch")
            st.button(NAV["start"], key="nav_start", on_click=new_run_screen, width="stretch")
            st.button(NAV["history"], key="nav_history", on_click=go, args=("history",), width="stretch")
        with panel("peach", "ongoing"):
            render_ongoing()


def banner(text: str) -> None:
    st.markdown(f'<div class="banner">{html.escape(text)}</div>', unsafe_allow_html=True)


def stat_card(color: str, label: str, value, note: str = "") -> str:
    return (f'<div class="stat stat-{color}"><div class="stat-label">{html.escape(label)}</div>'
            f'<div class="stat-value">{html.escape(str(value))}</div>'
            f'<div class="stat-note">{html.escape(note)}</div></div>')


def chip(kind: str, text: str) -> str:
    return f'<span class="chip chip-{kind}">{html.escape(text)}</span>'


def go(screen: str) -> None:
    """Button callback: switch screen."""
    st.session_state.screen = screen
    st.session_state.pop("error", None)


def new_run_screen() -> None:
    """Button callback: open the Start a run screen. An ongoing run is kept (and can be resumed)
    until a new run is actually started."""
    for key in ("editing", "edit_problems", "error"):
        st.session_state.pop(key, None)
    st.session_state.screen = "start"


def result_label(passed) -> str:
    """Status never depends on color alone: icon plus word."""
    return "Not run" if passed is None else "✔ Passed" if passed else "✘ Failed"


def _quoted(match: re.Match) -> str:
    return f'<span class="g-str">{match.group(1)}</span>'


def gherkin_html(text: str) -> str:
    """Gherkin as colored HTML for a white plate on a pastel card (colors and contrast: see CSS)."""
    out = []
    for raw in text.splitlines():
        line = html.escape(raw)
        stripped = line.lstrip()
        indent = line[: len(line) - len(stripped)]
        if stripped.startswith("@"):
            out.append(f'<span class="g-tag">{line}</span>')
            continue
        head, _, rest = stripped.partition(" ")
        if head == "Scenario:":
            out.append(f'{indent}<span class="g-kw">{head}</span> <b>{rest}</b>')
        elif head in ("Given", "When", "Then", "And", "But"):
            rest = re.sub(r"(&quot;.*?&quot;)", _quoted, rest)
            out.append(f'{indent}<span class="g-kw">{head}</span> {rest}')
        else:
            out.append(line)
    return '<pre class="gherkin" style="white-space: pre;">' + "\n".join(out) + "</pre>"


def stage_card_html(steps: list[str], state: str = "running") -> str:
    """Black card listing the stages so far. Returns "" until the first stage exists, so the card
    only appears once there is something to show. state: running | done | failed (for the last stage)."""
    if not steps:
        return ""
    rows = []
    for i, step in enumerate(steps):
        text = html.escape(step)
        if i < len(steps) - 1 or state == "done":
            rows.append(f'<div class="stage stage-done"><span class="stage-tick">&#10004;</span><span>{text}</span></div>')
        elif state == "failed":
            rows.append(f'<div class="stage stage-failed"><span>&#10008;</span><span>{text}</span></div>')
        else:
            rows.append(f'<div class="stage stage-now">{SPINNER}<span>{text}&hellip;</span></div>')
    return '<div class="stage-card" role="status">' + "".join(rows) + "</div>"


def pcard_html(kind: str, title: str, sub: str = "", level: int = 2) -> str:
    """A pastel card (kind: pink | peach | blue | lilac | grey) holding a heading and optional sub-text."""
    sub_html = f"<p>{html.escape(sub)}</p>" if sub else ""
    return f'<div class="pcard pcard-{kind}"><h{level}>{html.escape(title)}</h{level}>{sub_html}</div>'


def title_card(title: str, sub: str = "", kind: str = "grey", level: int = 2) -> None:
    """Page heading card. Page headings use a light coral (#FFE3E3) card with coral heading text; no other card uses this tint."""
    st.html(pcard_html(kind, title, sub, level))


def note_card(inner_html: str, kind: str = "lilac") -> None:
    """A pastel card holding one line of text. `inner_html` must already be escaped by the caller."""
    st.html(f'<div class="pcard pcard-{kind}"><p style="margin: 0;">{inner_html}</p></div>')


def panel(kind: str, name: str):
    """A pastel container for text plus widgets (radio buttons, tables, buttons)."""
    return st.container(key=f"pcard_{kind}_{name}")
