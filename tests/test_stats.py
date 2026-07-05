from doctest_ai.stats import (
    bootstrap_delta,
    per_task_deltas,
    wilson_interval,
)


def _record(task_id, arm, rep, passed, first=None):
    return {
        "task_id": task_id,
        "arm": arm,
        "rep": rep,
        "passed": passed,
        "first_attempt_passed": passed if first is None else first,
    }


def make_records(rates: dict[str, dict[str, list[bool]]]) -> list[dict]:
    """rates: {arm: {task: [outcomes]}}"""
    records = []
    for arm, tasks in rates.items():
        for task, outcomes in tasks.items():
            for rep, passed in enumerate(outcomes):
                records.append(_record(task, arm, rep, passed))
    return records


def test_wilson_interval_basic():
    lo, hi = wilson_interval(5, 10)
    assert 0.0 < lo < 0.5 < hi < 1.0


def test_wilson_interval_empty():
    assert wilson_interval(0, 0) == (0.0, 1.0)


def test_wilson_interval_bounds():
    lo, hi = wilson_interval(10, 10)
    assert hi == 1.0
    assert lo > 0.5


def test_bootstrap_delta_maximal():
    records = make_records(
        {
            "none": {f"t{i}": [False] * 5 for i in range(3)},
            "docs": {f"t{i}": [True] * 5 for i in range(3)},
        }
    )
    delta = bootstrap_delta(records, "none", "docs", n_boot=200, seed=1)
    assert delta.point == 1.0
    assert delta.ci_low == delta.ci_high == 1.0
    assert delta.significant


def test_bootstrap_delta_zero():
    records = make_records(
        {
            "none": {f"t{i}": [True, False] * 3 for i in range(4)},
            "docs": {f"t{i}": [True, False] * 3 for i in range(4)},
        }
    )
    delta = bootstrap_delta(records, "none", "docs", n_boot=500, seed=1)
    assert delta.point == 0.0
    assert not delta.significant


def test_bootstrap_delta_point_estimate():
    records = make_records(
        {
            "none": {"a": [False, False], "b": [True, True]},
            "docs": {"a": [True, True], "b": [True, True]},
        }
    )
    delta = bootstrap_delta(records, "none", "docs", n_boot=100, seed=0)
    assert delta.point == 0.5  # mean of per-task deltas (1.0 and 0.0)
    assert delta.n_tasks == 2


def test_per_task_deltas_sorted_descending():
    records = make_records(
        {
            "none": {"easy": [True, True], "hard": [False, False]},
            "docs": {"easy": [True, True], "hard": [True, True]},
        }
    )
    rows = per_task_deltas(records, "none", "docs")
    assert [r["task_id"] for r in rows] == ["hard", "easy"]
    assert rows[0]["delta"] == 1.0
    assert rows[1]["delta"] == 0.0
