import json

CONFTEST = """
import pytest

from doctest_ai.agent import AgentResult, FakeAgent
from doctest_ai.docs import DocsSpec, NoDocs


class MarkerDocs:
    def apply(self, workspace):
        return DocsSpec(prompt_preamble="CONSULT-THE-DOCS")


@pytest.fixture
def workspace_env():
    return None  # skip venv creation; FakeAgent never shells out


@pytest.fixture
def docs_sources():
    return {"none": NoDocs(), "docs": MarkerDocs()}


@pytest.fixture
def agent_backend_factory():
    def factory(settings, spec):
        def script(prompt, cwd):
            ok = "CONSULT-THE-DOCS" in prompt
            (cwd / "result.txt").write_text("ok" if ok else "bad")
            return AgentResult(success=True, output="done", cost_usd=0.01, num_turns=2)

        return FakeAgent(script=script)

    return factory
"""

TASK_FILE = """
import doctest_ai


@doctest_ai.task(id="marker-task", arms=["none", "docs"])
def test_marker(agent, workspace):
    agent.run("do the thing")
    assert (workspace / "result.txt").read_text() == "ok"
"""


def test_arms_and_reps_parametrization(pytester):
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(TASK_FILE)
    artifact = pytester.path / "results.jsonl"
    result = pytester.runpytest(
        "--doctest-reps=2", f"--doctest-artifact={artifact}", "-v"
    )
    # docs arm passes (preamble present), none arm fails: 2 reps each
    result.assert_outcomes(passed=2, failed=2)

    records = [json.loads(line) for line in artifact.read_text().splitlines()]
    assert len(records) == 4
    by_arm = {}
    for record in records:
        assert record["task_id"] == "marker-task"
        assert record["cost_usd"] > 0
        by_arm.setdefault(record["arm"], []).append(record)
    assert sorted(by_arm) == ["docs", "none"]
    assert all(r["passed"] for r in by_arm["docs"])
    assert all(not r["passed"] for r in by_arm["none"])
    assert all(r["first_attempt_passed"] is False for r in by_arm["none"])
    assert sorted(r["rep"] for r in by_arm["docs"]) == [0, 1]


def test_cli_arm_override(pytester):
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(TASK_FILE)
    result = pytester.runpytest("--docs-arm=docs")
    result.assert_outcomes(passed=1)


def test_unknown_arm_fails_clearly(pytester):
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(TASK_FILE)
    result = pytester.runpytest("--docs-arm=bogus")
    result.assert_outcomes(errors=1)
    result.stdout.fnmatch_lines(["*has no DocsSource*"])


def test_resume_skips_completed_runs(pytester):
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(TASK_FILE)
    artifact = pytester.path / "results.jsonl"
    result = pytester.runpytest(
        "--docs-arm=docs", "--doctest-reps=2", f"--doctest-artifact={artifact}"
    )
    result.assert_outcomes(passed=2)

    # Same command again with --doctest-resume: nothing reruns, no new records.
    result = pytester.runpytest(
        "--docs-arm=docs",
        "--doctest-reps=2",
        f"--doctest-artifact={artifact}",
        "--doctest-resume",
    )
    result.assert_outcomes(skipped=2)
    assert len(artifact.read_text().splitlines()) == 2

    # A higher rep count only runs the missing reps.
    result = pytester.runpytest(
        "--docs-arm=docs",
        "--doctest-reps=3",
        f"--doctest-artifact={artifact}",
        "--doctest-resume",
    )
    result.assert_outcomes(passed=1, skipped=2)
    records = [json.loads(line) for line in artifact.read_text().splitlines()]
    assert sorted(r["rep"] for r in records) == [0, 1, 2]


AGENT_ERROR_CONFTEST = """
from pathlib import Path

import pytest

from doctest_ai.agent import AgentError, AgentResult, FakeAgent
from doctest_ai.docs import NoDocs

HEALTHY = Path(__file__).parent / "healthy"


@pytest.fixture
def workspace_env():
    return None  # skip venv creation; FakeAgent never shells out


@pytest.fixture
def agent_backend_factory():
    def factory(settings, spec):
        def script(prompt, cwd):
            if not HEALTHY.exists():
                raise AgentError("Claude Code run failed: usage limit reached")
            (cwd / "out.txt").write_text("good")
            return AgentResult(success=True, cost_usd=0.01, num_turns=2)

        return FakeAgent(script=script)

    return factory
"""

AGENT_ERROR_TASK = """
import doctest_ai


@doctest_ai.task(id="fragile-task")
def test_fragile(agent, workspace):
    def check():
        assert (workspace / "out.txt").read_text() == "good"

    agent.solve("produce out.txt", check)
"""


def test_agent_error_recorded_without_outcome_and_retried_on_resume(pytester):
    pytester.makeconftest(AGENT_ERROR_CONFTEST)
    pytester.makepyfile(AGENT_ERROR_TASK)
    artifact = pytester.path / "results.jsonl"

    # Runtime failure: the test errors, but the record carries no outcome.
    result = pytester.runpytest(f"--doctest-artifact={artifact}")
    result.assert_outcomes(failed=1)
    (record,) = [json.loads(line) for line in artifact.read_text().splitlines()]
    assert record["passed"] is None
    assert record["first_attempt_passed"] is None
    assert "usage limit" in record["error"]

    # Once the runtime is healthy, --doctest-resume retries that run.
    (pytester.path / "healthy").touch()
    result = pytester.runpytest(f"--doctest-artifact={artifact}", "--doctest-resume")
    result.assert_outcomes(passed=1)
    records = [json.loads(line) for line in artifact.read_text().splitlines()]
    assert len(records) == 2
    assert records[-1]["passed"] is True


def test_solve_retry_loop_records_attempts(pytester):
    pytester.makeconftest(
        """
import pytest

from doctest_ai.agent import AgentResult, FakeAgent
from doctest_ai.docs import NoDocs


@pytest.fixture
def workspace_env():
    return None  # skip venv creation; FakeAgent never shells out


@pytest.fixture
def agent_backend_factory():
    def factory(settings, spec):
        def script(prompt, cwd):
            if prompt.startswith("fix this error"):
                (cwd / "out.txt").write_text("good")
            else:
                (cwd / "out.txt").write_text("bad")
            return AgentResult(success=True, cost_usd=0.01)

        return FakeAgent(script=script)

    return factory
"""
    )
    pytester.makefile(
        ".toml", pyproject='[tool."doctest-ai"]\nmax_retries = 2\n'
    )
    pytester.makepyfile(
        """
import doctest_ai


@doctest_ai.task(id="retry-task")
def test_retry(agent, workspace):
    def check():
        assert (workspace / "out.txt").read_text() == "good"

    agent.solve("produce out.txt", check)
"""
    )
    artifact = pytester.path / "results.jsonl"
    result = pytester.runpytest(f"--doctest-artifact={artifact}")
    result.assert_outcomes(passed=1)

    (record,) = [json.loads(line) for line in artifact.read_text().splitlines()]
    assert record["passed"] is True
    assert record["first_attempt_passed"] is False  # needed the retry loop
    assert record["attempts"] == 2  # initial run + one fix
