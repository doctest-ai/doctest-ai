"""Kedro 1.x tasks — the efficiency suite.

Pre-registered framing (decided 2026-07-06, before the full batch): the
primary metrics for this suite are EFFICIENCY and RELIABILITY — turns and
cost among passing runs, plus success@1 — not the pass rate.

The original stale-priors hypothesis (agents write pre-1.0 Kedro code and
fail without docs) did not survive the signal check: current models recover
via priors, reading installed source, and iterating against `kedro run`
errors, so both arms pass. What the signal check did show is a large spread
in *how* they pass (no-docs: 46 turns/$1.24 brute-forcing runner semantics;
docs: fewer turns via targeted MCP lookups). Runs are capped at a
pre-registered turn budget (see conftest) as cost control; a run that
exhausts the budget is recorded as a failure and disclosed as such.
"""

import doctest_ai
from suites.kedro.conftest import ARMS, KEDRO_PIN


def _new_project(run_cmd, workspace, example):
    res = run_cmd(
        "kedro",
        "new",
        "--name",
        "Project Dummy",
        "--tools",
        "none",
        "--example",
        example,
    )
    assert res.returncode == 0, res.stdout + res.stderr
    return workspace / "project-dummy"


@doctest_ai.task(id="kedro-integration-test", arms=ARMS)
def test_write_integration_test(agent, workspace, install, run_cmd):
    """Ported from examples/kedro: write a test for the example pipeline."""
    install(KEDRO_PIN, "pytest")
    project = _new_project(run_cmd, workspace, example="yes")
    agent.cwd = project

    def check():
        res = run_cmd("uv", "pip", "install", "-e", ".", cwd=project)
        assert res.returncode == 0, res.stdout + res.stderr
        res = run_cmd("pytest", cwd=project)
        assert res.returncode == 0, res.stdout + res.stderr

    agent.solve(
        "write an integration test for the data science pipeline", check
    )


@doctest_ai.task(id="kedro-new-pipeline", arms=ARMS)
def test_create_and_register_pipeline(agent, workspace, install, run_cmd):
    # Verifier vetted on kedro 1.5.0: a hand-written pipelines/report package
    # (auto-discovered) exits 0; the bare project exits 1 (no nodes).
    install(KEDRO_PIN)
    project = _new_project(run_cmd, workspace, example="no")
    agent.cwd = project

    def check():
        res = run_cmd("kedro", "run", cwd=project)
        assert res.returncode == 0, res.stdout + res.stderr

    agent.solve(
        "create a pipeline named 'report' containing a single node that "
        "returns the string 'ok' as an output named 'report_status', register "
        "it so it runs as part of the default pipeline, and make sure "
        "`kedro run` succeeds",
        check,
    )
