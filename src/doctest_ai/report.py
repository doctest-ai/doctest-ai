"""Render a Docs Delta report (Markdown) from a JSONL run artifact."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from doctest_ai.stats import (
    bootstrap_delta,
    load_records,
    outcomes_by_task,
    pass_rate,
    per_task_deltas,
    wilson_interval,
)


def _pct(x: float) -> str:
    return f"{100 * x:.0f}%"


def _pts(x: float) -> str:
    return f"{100 * x:+.0f}pts"


def build_report(records: list[dict], baseline: str = "none") -> str:
    arms = sorted({r["arm"] for r in records})
    models = sorted({r["model"] for r in records if r.get("model")})
    total_cost = sum(r.get("cost_usd") or 0.0 for r in records)

    lines = [
        "# Docs Delta report",
        "",
        f"- Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        f"- Model(s): {', '.join(models) or 'unknown'}",
        f"- Runs: {len(records)} | Arms: {', '.join(arms)} | "
        f"Total agent cost: ${total_cost:.2f}",
        "",
        "## Pass rates by task and arm",
        "",
        "| Task | Arm | Passed | Rate [95% CI] | success@1 |",
        "|---|---|---|---|---|",
    ]

    for arm in arms:
        by_task = outcomes_by_task(records, arm)
        first = outcomes_by_task(records, arm, metric="first_attempt_passed")
        for task in sorted(by_task):
            outcomes = by_task[task]
            k, n = sum(outcomes), len(outcomes)
            lo, hi = wilson_interval(k, n)
            s1 = pass_rate(first.get(task, []))
            lines.append(
                f"| {task} | {arm} | {k}/{n} | "
                f"{_pct(k / n)} [{_pct(lo)}, {_pct(hi)}] | {_pct(s1)} |"
            )

    treatment_arms = [a for a in arms if a != baseline]
    if baseline in arms and treatment_arms:
        lines += ["", f"## Docs Delta (vs `{baseline}`)", ""]
        for arm in treatment_arms:
            try:
                delta = bootstrap_delta(records, baseline, arm)
            except ValueError:
                continue
            verdict = "significant" if delta.significant else "not significant"
            lines += [
                f"### `{arm}`: **{_pts(delta.point)}** "
                f"[{_pts(delta.ci_low)}, {_pts(delta.ci_high)}] "
                f"({verdict}; {delta.n_tasks} tasks, paired bootstrap)",
                "",
                "| Task | Rate (baseline) | Rate (arm) | Delta |",
                "|---|---|---|---|",
            ]
            for row in per_task_deltas(records, baseline, arm):
                lines.append(
                    f"| {row['task_id']} | {_pct(row['baseline_rate'])} "
                    f"| {_pct(row['arm_rate'])} | {_pts(row['delta'])} |"
                )
            lines.append("")

    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="doctest-ai")
    subparsers = parser.add_subparsers(dest="command", required=True)
    report = subparsers.add_parser(
        "report", help="Render a Docs Delta report from a JSONL run artifact."
    )
    report.add_argument("artifact", help="Path to the JSONL artifact.")
    report.add_argument("--baseline", default="none", help="Baseline arm name.")
    report.add_argument("--out", default=None, help="Write to file (default stdout).")
    args = parser.parse_args(argv)

    records = load_records(args.artifact)
    output = build_report(records, baseline=args.baseline)
    if args.out:
        Path(args.out).write_text(output)
    else:
        sys.stdout.write(output)
    return 0
