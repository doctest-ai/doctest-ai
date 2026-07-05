"""pytest plugin: task API, arms x reps parametrization, and result recording.

A doctest-ai *task* is a plain pytest test decorated with
``@doctest_ai.task(...)`` that receives an ``agent`` and a ``workspace``. The
plugin parametrizes each task across docs arms (which ``DocsSource`` the agent
gets) and repetitions, and appends one JSONL record per run to the artifact
for the ablation statistics.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from doctest_ai._config import ClaudeCodeSettings, Settings
from doctest_ai.agent import DEFAULT_MODEL, ClaudeAgent
from doctest_ai.docs import DocsSpec, NoDocs
from doctest_ai.runner import Recorder, RunRecord, TaskAgent
from doctest_ai.sh_run import run

# --------------------------------------------------------------------------
# Isolated-venv machinery (each run gets a clean virtual environment)
# --------------------------------------------------------------------------


def _setup_context_with_venv(context, venv_dir):
    context.venv_dir = venv_dir
    # note the locations of some useful stuff
    # this is because exe resolution in subprocess doesn't respect a passed env
    if os.name == "posix":
        bin_dir = context.venv_dir / "bin"
    else:
        bin_dir = context.venv_dir / "Scripts"
    context.bin_dir = bin_dir
    context.python = str(bin_dir / "python")

    # clone the environment, remove any condas and venvs and insert our venv
    context.env = os.environ.copy()
    path = context.env["PATH"].split(os.pathsep)
    path = [p for p in path if not (Path(p).parent / "pyvenv.cfg").is_file()]
    path = [p for p in path if not (Path(p).parent / "conda-meta").is_dir()]
    path = [str(bin_dir), *path]
    context.env["PATH"] = os.pathsep.join(path)

    # specify the virtual environment to install into
    context.env["VIRTUAL_ENV"] = str(context.venv_dir)


def _create_new_venv(request) -> Path:
    """Create a new venv.

    Returns:
        path to created venv
    """
    tmp_path = request.getfixturevalue("tmp_path")
    run(["uv", "venv"], cwd=tmp_path, check=True)
    return tmp_path / ".venv"


def _setup_minimal_env(request):
    venv_dir = _create_new_venv(request)
    _setup_context_with_venv(request, venv_dir)


# --------------------------------------------------------------------------
# CLI options and configuration
# --------------------------------------------------------------------------


def pytest_addoption(parser):
    group = parser.getgroup("doctest-ai")
    group.addoption(
        "--docs-arm",
        dest="docs_arm",
        action="append",
        default=None,
        help="Docs arm(s) to run (repeatable); overrides the task's arm list.",
    )
    group.addoption(
        "--doctest-reps",
        dest="doctest_reps",
        type=int,
        default=None,
        help="Repetitions per (task, arm); agent runs are stochastic.",
    )
    group.addoption(
        "--doctest-artifact",
        dest="doctest_artifact",
        default=None,
        help="JSONL file to append one record per (task, arm, rep) run to.",
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "doctest_ai_task(task_id=..., arms=[...]): a doctest-ai agent task, "
        "parametrized across docs arms and repetitions.",
    )
    artifact = config.getoption("doctest_artifact") or Settings().artifact
    config._doctest_ai_recorder = Recorder(Path(artifact) if artifact else None)

    try:
        import pytest_bdd  # noqa: F401

        from doctest_ai import bdd

        config.pluginmanager.register(bdd, "doctest-ai-bdd")
    except ImportError:
        pass


def pytest_generate_tests(metafunc):
    marker = metafunc.definition.get_closest_marker("doctest_ai_task")
    if marker is None:
        return
    settings = Settings()
    arms = (
        metafunc.config.getoption("docs_arm")
        or marker.kwargs.get("arms")
        or settings.arms
        or ["none"]
    )
    reps = metafunc.config.getoption("doctest_reps") or settings.reps or 1
    if "docs_arm" in metafunc.fixturenames:
        metafunc.parametrize("docs_arm", arms)
    if "rep" in metafunc.fixturenames:
        metafunc.parametrize("rep", range(reps), ids=[f"rep{i}" for i in range(reps)])


# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------


@pytest.fixture
def settings():
    """Return the Claude Code settings."""
    return ClaudeCodeSettings()


@pytest.fixture
def docs_arm():
    """Which docs condition this run is under; parametrized per task."""
    return "none"


@pytest.fixture
def rep():
    """Repetition index; parametrized via --doctest-reps."""
    return 0


@pytest.fixture
def docs_sources():
    """Map arm name -> DocsSource. Suites override this in their conftest."""
    return {"none": NoDocs()}


@pytest.fixture
def workspace(request, tmp_path):
    """Isolated working directory (with its own venv) the agent acts on."""
    _setup_minimal_env(request)
    return tmp_path


@pytest.fixture
def agent_backend_factory():
    """Build the agent backend; override to swap runtimes (e.g. FakeAgent)."""

    def factory(settings: ClaudeCodeSettings, spec: DocsSpec):
        return ClaudeAgent(
            model=settings.model or DEFAULT_MODEL,
            allowed_tools=[*settings.allowed_tools, *spec.allowed_tools],
            disallowed_tools=settings.disallowed_tools,
            mcp_servers=spec.mcp_servers,
            max_turns=settings.max_turns,
        )

    return factory


@pytest.fixture
def agent(
    request, workspace, docs_arm, rep, docs_sources, settings, agent_backend_factory
):
    """The agent under the current docs arm, acting on ``workspace``."""
    try:
        source = docs_sources[docs_arm]
    except KeyError:
        pytest.fail(
            f"docs arm {docs_arm!r} has no DocsSource; "
            f"available arms: {sorted(docs_sources)}"
        )
    spec = source.apply(workspace)
    backend = agent_backend_factory(settings, spec)

    marker = request.node.get_closest_marker("doctest_ai_task")
    task_id = (
        (marker.kwargs.get("task_id") if marker else None)
        or getattr(request.node, "originalname", None)
        or request.node.name
    )
    record = RunRecord(
        task_id=task_id, arm=docs_arm, rep=rep, model=getattr(backend, "model", None)
    )
    request.node._doctest_ai_record = record
    recorder: Recorder = request.config._doctest_ai_recorder
    return TaskAgent(
        backend,
        cwd=workspace,
        env=getattr(request, "env", None),
        record=record,
        preamble=spec.prompt_preamble,
        max_retries=Settings().max_retries or 0,
        transcript_dir=recorder.transcript_dir,
    )


# --------------------------------------------------------------------------
# Result recording
# --------------------------------------------------------------------------


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when != "call":
        return
    record: RunRecord | None = getattr(item, "_doctest_ai_record", None)
    if record is None:
        return
    record.passed = report.passed
    record.duration_s = report.duration
    if report.failed:
        record.error = str(report.longrepr)[-2000:]
    if record.first_attempt_passed is None:
        record.first_attempt_passed = report.passed
    item.config._doctest_ai_recorder.write(record)
