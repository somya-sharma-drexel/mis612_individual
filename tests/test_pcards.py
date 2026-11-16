"""Pastel card helpers."""
import pytest

from agent_app.ui.theme import pcard_html


@pytest.mark.parametrize("kind", ["pink", "peach", "blue", "lilac"])
def test_card_kinds_and_levels(kind):
    out = pcard_html(kind, "Title", "Sub", level=3)
    assert f"pcard pcard-{kind}" in out and "<h3>Title</h3>" in out and "<p>Sub</p>" in out


def test_card_without_subtext_has_no_paragraph_and_escapes_html():
    out = pcard_html("pink", "<b>x</b>")
    assert "&lt;b&gt;x&lt;/b&gt;" in out and "<p>" not in out


def test_page_headings_default_to_grey_and_grey_is_used_nowhere_else():
    import pathlib
    import re

    assert "pcard pcard-grey" in pcard_html("grey", "Title")
    ui = pathlib.Path(__file__).resolve().parent.parent / "agent_app" / "ui"
    uses = {f.name: re.findall(r"grey", f.read_text(encoding="utf-8")) for f in ui.glob("*.py")}
    # Only the theme (definition + title_card default) mentions grey: no screen picks it by hand.
    assert all(not v for k, v in uses.items() if k != "theme.py"), uses


def test_page_heading_cards_are_centered_by_css():
    from agent_app.ui.theme import CSS

    assert ".pcard-grey, .pcard-grey h1" in CSS and "text-align: center" in CSS.split(".pcard-grey, .pcard-grey h1")[1].split("}")[0]


def test_page_heading_text_is_coral_on_light_coral():
    from agent_app.ui.theme import CSS

    rule = CSS.split(".pcard-grey h1, .pcard-grey h2, .pcard-grey h3 { color: ")[1].split(";")[0]
    assert rule == "#FF5151" and ".pcard-grey { background: #FFE3E3; }" in CSS


def test_sidebar_brand_uses_the_page_heading_scheme():
    import inspect

    from agent_app.ui import theme

    src = inspect.getsource(theme.render_sidebar)
    assert "pcard pcard-grey brand" in src and ".pcard-grey.brand { color: #FF5151;" in theme.CSS


def test_stat_cards_are_black_with_light_text():
    from agent_app.ui.theme import CSS, stat_card

    assert "stat-value" in stat_card("peach", "Total runs", 3, "All time")
    block = CSS.split("/* Stat cards")[1].split("/* Decision chips")[0]
    assert "background: #0A0A0A" in block and "color: #FFFFFF" in block and "#B4B8CC" in block
    assert ".stat-value { font-weight: 800; font-size: 2.4rem; line-height: 1.2; color: #FF5151; }" in block  # coral numbers


def test_sidebar_brand_is_left_aligned():
    from agent_app.ui.theme import CSS

    rule = CSS.split(".pcard-grey.brand {")[1].split("}")[0]
    assert "justify-content: flex-start" in rule and "text-align: left" in rule


def test_cards_are_black_at_70_percent_transparency():
    import re

    from agent_app.ui.theme import CSS

    glass = "rgba(0, 0, 0, 0.3)"  # 70% transparent black
    for kind in ("pink", "peach", "blue", "lilac"):
        assert f".pcard-{kind} {{ background: {glass}; }}" in CSS
        assert f'[class*="st-key-pcard_{kind}_"] {{ background: {glass}; }}' in CSS
    assert f".stage-card {{ background: {glass};" in CSS
    # No pastel fill is left behind; only the grey heading card, white plates and the solid black stat cards remain.
    fills = re.findall(r"background: (#[0-9A-Fa-f]{6})", CSS.split("/* Stat cards")[0].split("/* Cards for page text")[1])
    assert not {f.upper() for f in fills} & {"#FDEBF9", "#FFE7DF", "#E8F0FB", "#EFE9FB"}


def test_app_uses_playfair_display_everywhere_except_gherkin_code():
    from agent_app.ui.theme import CSS

    assert "family=Playfair+Display" in CSS and "Plus+Jakarta" not in CSS and "Plus Jakarta" not in CSS
    assert ".stApp *:not([data-testid=\"stIconMaterial\"])" in CSS  # every element except Material icons
    assert "font-family: 'Playfair Display', Georgia" in CSS and "font-variant-numeric: lining-nums" in CSS
    assert "pre.gherkin, pre.gherkin * { font-family: Consolas" in CSS  # code plate stays monospace


def test_blue_text_is_0047AB():
    from agent_app.ui.theme import CSS

    assert ".g-kw { color: #0047AB; font-weight: 700; }" in CSS and "#2F4BD8" not in CSS
    assert "a { color: #0047AB; }" in CSS


def test_no_ongoing_runs_matches_the_menu_button_size():
    from agent_app.ui.theme import CSS

    rule = CSS.split('[data-testid="stSidebar"] .muted, [data-testid="stSidebar"] .ongoing-row {')[1].split("}")[0]
    assert "font-size: 14px" in rule and "font-weight: 400" in rule
