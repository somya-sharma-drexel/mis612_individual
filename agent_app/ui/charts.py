"""Run-status donut chart as inline SVG (no JavaScript, works inside Streamlit markdown).

The chart sits on a white plate inside a pastel card. Colors passed the dataviz validator on white
(lightness band, chroma, CVD separation, 3:1 contrast): Pass #3B5BDB, Partial #9A7BE0, Fail #FF5151.
Identity never rests on color alone: the legend shows an icon, the word, the count and the share;
each segment has a hover title. Text is navy (set in CSS), never the series color.
"""
import html
import math

STATUSES = [  # fixed order, matches the legend
    ("Pass", "✔", "#3B5BDB"),
    ("Partial", "◐", "#9A7BE0"),
    ("Fail", "✘", "#FF5151"),
]
RADIUS, STROKE, GAP = 44, 18, 2.0  # GAP: 2px surface gap between segments
CIRC = 2 * math.pi * RADIUS


def count_statuses(runs: list[dict]) -> dict[str, int]:
    """Runs that finished with a result; other statuses (Rejected, Drafted, ...) are not charted."""
    return {name: sum(1 for r in runs if r["status"] == name) for name, _, _ in STATUSES}


def status_donut(counts: dict[str, int]) -> str:
    """HTML for the donut with the total in the middle and a legend on the right."""
    total = sum(counts.values())
    segments, offset = [], 0.0
    active = [s for s in STATUSES if counts.get(s[0])]
    for name, _, color in active:
        share = counts[name] / total
        length = share * CIRC
        drawn = length if len(active) == 1 else max(length - GAP, 0.5)
        segments.append(
            f'<circle cx="60" cy="60" r="{RADIUS}" fill="none" stroke="{color}" stroke-width="{STROKE}" '
            f'stroke-dasharray="{drawn:.2f} {CIRC - drawn:.2f}" stroke-dashoffset="{-offset:.2f}" '
            f'transform="rotate(-90 60 60)"><title>{name}: {counts[name]} of {total} '
            f'({share:.0%})</title></circle>')
        offset += length
    ring = "".join(segments) or (
        f'<circle cx="60" cy="60" r="{RADIUS}" fill="none" stroke="#E3E5EE" stroke-width="{STROKE}"/>')
    svg = (f'<svg viewBox="0 0 120 120" width="150" height="150" role="img" '
           f'aria-label="Run results: {html.escape(_summary(counts, total))}">{ring}'
           f'<text x="60" y="58" text-anchor="middle" class="donut-total">{total}</text>'
           f'<text x="60" y="74" text-anchor="middle" class="donut-sub">runs</text></svg>')
    rows = "".join(
        f'<div class="legend-row"><span class="legend-dot" style="background:{color}"></span>'
        f'<span class="legend-name">{icon} {name}</span>'
        f'<span class="legend-val">{counts.get(name, 0)}'
        f'<span class="muted"> · {(counts.get(name, 0) / total if total else 0):.0%}</span></span></div>'
        for name, icon, color in STATUSES)
    return f'<div class="donut-wrap">{svg}<div class="legend">{rows}</div></div>'


def _summary(counts: dict[str, int], total: int) -> str:
    return ", ".join(f"{n} {counts.get(n, 0)}" for n, _, _ in STATUSES) + f" of {total}"
