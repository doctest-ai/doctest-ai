"""Kedro 1.x tasks — the stale-priors headliner.

Without docs, agents tend to produce pre-1.0 Kedro code (old ConfigLoader,
old project layout, removed CLI flags); the docs arm should rescue them.
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
