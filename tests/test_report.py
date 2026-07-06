from doctest_ai.report import build_report
from test_stats import make_records


def test_build_report_sections():
    records = make_records(
        {
            "none": {"t1": [False] * 4, "t2": [True] * 4},
            "docs": {"t1": [True] * 4, "t2": [True] * 4},
        }
    )
    for record in records:
        record["model"] = "claude-sonnet-5"
        record["cost_usd"] = 0.05
    report = build_report(records, baseline="none")
    assert "# Docs Delta report" in report
    assert "claude-sonnet-5" in report
    assert "## Arm summaries" in report
    assert "| docs | 8 | 8/8 | $0.05 | 0 |" in report
    assert "| t1 | none | 0/4 |" in report
    assert "| t1 | docs | 4/4 |" in report
    assert "## Docs Delta (vs `none`)" in report
    assert "+50pts" in report  # mean of per-task deltas (+100 and 0)


def test_build_report_efficiency_section():
    records = make_records(
        {
            "none": {"t1": [True] * 4, "t2": [True] * 4},
            "docs": {"t1": [True] * 4, "t2": [True] * 4},
        }
    )
    for record in records:
        record["model"] = "claude-sonnet-5"
        record["cost_usd"] = 0.60 if record["arm"] == "none" else 0.20
        record["num_turns"] = 30 if record["arm"] == "none" else 10
    report = build_report(records, baseline="none")
    assert "## Efficiency Delta (among passing runs, vs `none`)" in report
    assert "-20.0*" in report  # turns delta, CI excludes zero
    assert "-$0.40*" in report  # cost delta, CI excludes zero


def test_build_report_efficiency_section_needs_metric_data():
    records = make_records(
        {
            "none": {"t1": [True] * 2},
            "docs": {"t1": [True] * 2},
        }
    )
    report = build_report(records, baseline="none")
    assert "Efficiency Delta" not in report  # no turns/cost recorded


def test_build_report_without_baseline_arm():
    records = make_records({"docs": {"t1": [True, False]}})
    report = build_report(records, baseline="none")
    assert "Docs Delta (vs" not in report  # no baseline data -> no delta section
    assert "| t1 | docs | 1/2 |" in report
