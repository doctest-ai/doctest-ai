"""Ablation statistics: pass rates, intervals, and the Docs Delta.

Agent runs are stochastic, so every number ships with uncertainty:
per-(task, arm) pass rates carry Wilson intervals, and the headline suite
delta carries a paired two-level bootstrap CI (resampling tasks, then reps
within each task). Per-task deltas are reported as flip tables without
significance claims — per-task rep counts are too small for honest p-values.
"""

from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass
from pathlib import Path


def load_records(path: str | Path) -> list[dict]:
    records = []
    with Path(path).open() as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def wilson_interval(
    successes: int, n: int, z: float = 1.96
) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion."""
    if n == 0:
        return (0.0, 1.0)
    p = successes / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    margin = (z / denom) * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))
    return (max(0.0, center - margin), min(1.0, center + margin))


def outcomes_by_task(
    records: list[dict], arm: str, metric: str = "passed"
) -> dict[str, list[bool]]:
    """Map task_id -> list of boolean outcomes (one per rep) for one arm."""
    result: dict[str, list[bool]] = {}
    for record in records:
        if record["arm"] != arm or record.get(metric) is None:
            continue
        result.setdefault(record["task_id"], []).append(bool(record[metric]))
    return result


def pass_rate(outcomes: list[bool]) -> float:
    return sum(outcomes) / len(outcomes) if outcomes else 0.0


def values_by_task(
    records: list[dict], arm: str, metric: str, *, passed_only: bool = True
) -> dict[str, list[float]]:
    """Map task_id -> numeric metric values (one per rep) for one arm."""
    result: dict[str, list[float]] = {}
    for record in records:
        if record["arm"] != arm or record.get(metric) is None:
            continue
        if passed_only and not record.get("passed"):
            continue
        result.setdefault(record["task_id"], []).append(float(record[metric]))
    return result


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _paired_bootstrap(
    base: dict[str, list[float]],
    treat: dict[str, list[float]],
    tasks: list[str],
    n_boot: int,
    seed: int,
) -> tuple[float, float, float]:
    """Two-level bootstrap of the mean per-task difference ``treat - base``."""
    point = sum(_mean(treat[t]) - _mean(base[t]) for t in tasks) / len(tasks)
    rng = random.Random(seed)
    deltas = []
    for _ in range(n_boot):
        sampled_tasks = [tasks[rng.randrange(len(tasks))] for _ in tasks]
        total = 0.0
        for t in sampled_tasks:
            b, a = base[t], treat[t]
            rb = sum(b[rng.randrange(len(b))] for _ in b) / len(b)
            ra = sum(a[rng.randrange(len(a))] for _ in a) / len(a)
            total += ra - rb
        deltas.append(total / len(sampled_tasks))
    deltas.sort()
    lo = deltas[max(0, int(0.025 * n_boot))]
    hi = deltas[min(n_boot - 1, int(0.975 * n_boot))]
    return point, lo, hi


@dataclass
class DeltaEstimate:
    """Suite-level docs contribution: mean per-task pass-rate difference."""

    arm: str
    baseline: str
    point: float
    ci_low: float
    ci_high: float
    n_tasks: int
    n_boot: int

    @property
    def significant(self) -> bool:
        """Whether the 95% CI excludes zero."""
        return self.ci_low > 0 or self.ci_high < 0


def bootstrap_delta(
    records: list[dict],
    baseline: str,
    arm: str,
    *,
    metric: str = "passed",
    n_boot: int = 2000,
    seed: int = 0,
) -> DeltaEstimate:
    """Paired two-level bootstrap of the suite delta ``arm - baseline``.

    Pairing by task removes between-task difficulty variance from the
    estimate; the two levels (tasks, then reps within a task) account for
    both task sampling and run-to-run stochasticity.
    """
    base = outcomes_by_task(records, baseline, metric)
    treat = outcomes_by_task(records, arm, metric)
    tasks = sorted(set(base) & set(treat))
    if not tasks:
        raise ValueError(
            f"no tasks have data in both arms {baseline!r} and {arm!r}"
        )

    point, lo, hi = _paired_bootstrap(base, treat, tasks, n_boot, seed)
    return DeltaEstimate(
        arm=arm,
        baseline=baseline,
        point=point,
        ci_low=lo,
        ci_high=hi,
        n_tasks=len(tasks),
        n_boot=n_boot,
    )


@dataclass
class MetricDelta:
    """Suite-level difference in a numeric per-run metric (arm - baseline)."""

    arm: str
    baseline: str
    metric: str
    point: float
    ci_low: float
    ci_high: float
    n_tasks: int
    n_boot: int
    passed_only: bool

    @property
    def significant(self) -> bool:
        """Whether the 95% CI excludes zero."""
        return self.ci_low > 0 or self.ci_high < 0


def bootstrap_metric_delta(
    records: list[dict],
    baseline: str,
    arm: str,
    *,
    metric: str = "num_turns",
    passed_only: bool = True,
    n_boot: int = 2000,
    seed: int = 0,
) -> MetricDelta:
    """Paired two-level bootstrap of a numeric metric's suite delta.

    The efficiency counterpart to :func:`bootstrap_delta`: on suites where
    both arms pass, docs can still buy fewer turns and lower cost. By default
    only passing runs contribute — a failed run's turn count measures where
    the agent gave up, not what success costs — so the claim reads "among
    successful runs". Tasks without a passing run in both arms drop out of
    the pairing.
    """
    base = values_by_task(records, baseline, metric, passed_only=passed_only)
    treat = values_by_task(records, arm, metric, passed_only=passed_only)
    tasks = sorted(set(base) & set(treat))
    if not tasks:
        raise ValueError(
            f"no tasks have {metric!r} data in both arms {baseline!r} and {arm!r}"
        )

    point, lo, hi = _paired_bootstrap(base, treat, tasks, n_boot, seed)
    return MetricDelta(
        arm=arm,
        baseline=baseline,
        metric=metric,
        point=point,
        ci_low=lo,
        ci_high=hi,
        n_tasks=len(tasks),
        n_boot=n_boot,
        passed_only=passed_only,
    )


def per_task_deltas(
    records: list[dict], baseline: str, arm: str, metric: str = "passed"
) -> list[dict]:
    """Per-task rate comparison for the flip table (no significance claims)."""
    base = outcomes_by_task(records, baseline, metric)
    treat = outcomes_by_task(records, arm, metric)
    rows = []
    for task in sorted(set(base) & set(treat)):
        rate_base = pass_rate(base[task])
        rate_arm = pass_rate(treat[task])
        rows.append(
            {
                "task_id": task,
                "baseline_rate": rate_base,
                "arm_rate": rate_arm,
                "delta": rate_arm - rate_base,
                "n_baseline": len(base[task]),
                "n_arm": len(treat[task]),
            }
        )
    rows.sort(key=lambda r: r["delta"], reverse=True)
    return rows
