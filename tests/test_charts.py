"""Run-status donut: counting, geometry and accessible text."""
import re

from agent_app.ui.charts import CIRC, count_statuses, status_donut


def runs(*statuses):
    return [{"status": s} for s in statuses]


def test_counts_only_charted_statuses():
    counts = count_statuses(runs("Pass", "Pass", "Partial", "Fail", "Rejected", "Drafted", "Pushed – not executed"))
    assert counts == {"Pass": 2, "Partial": 1, "Fail": 1}


def test_legend_has_icon_word_count_and_share():
    out = status_donut({"Pass": 2, "Partial": 1, "Fail": 1})
    for text in ("✔ Pass", "◐ Partial", "✘ Fail", "50%", "25%"):
        assert text in out


def test_segments_sum_to_full_ring_minus_gaps():
    out = status_donut({"Pass": 2, "Partial": 1, "Fail": 1})
    drawn = [float(x) for x in re.findall(r'stroke-dasharray="([\d.]+) ', out)]
    assert len(drawn) == 3
    assert abs(sum(drawn) + 3 * 2.0 - CIRC) < 0.1  # 2px gap after each of 3 segments


def test_single_status_is_a_full_ring_without_gap():
    out = status_donut({"Pass": 3, "Partial": 0, "Fail": 0})
    drawn = [float(x) for x in re.findall(r'stroke-dasharray="([\d.]+) ', out)]
    assert drawn == [round(CIRC, 2)]


def test_empty_state_has_gray_ring_and_zero_total():
    out = status_donut({"Pass": 0, "Partial": 0, "Fail": 0})
    assert "#E3E5EE" in out and ">0<" in out and "stroke-dasharray" not in out


def test_dark_surface_styling_uses_css_classes_not_navy_fills():
    out = status_donut({"Pass": 1, "Partial": 0, "Fail": 0})
    assert 'class="donut-total"' in out and 'class="donut-sub"' in out and "#121843" not in out
    assert "#FF5151" in status_donut({"Pass": 0, "Partial": 0, "Fail": 1})


def test_accessible_label_and_hover_titles():
    out = status_donut({"Pass": 1, "Partial": 1, "Fail": 0})
    assert 'role="img"' in out and "aria-label" in out and "<title>Pass: 1 of 2 (50%)</title>" in out
