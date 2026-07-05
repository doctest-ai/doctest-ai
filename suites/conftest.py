"""Shared fixtures for all task suites."""

import pytest

from doctest_ai.sh_run import run


@pytest.fixture
def install(workspace, workspace_env):
    """Install packages into the task workspace's isolated venv."""

    def _install(*packages):
        res = run(
            ["uv", "pip", "install", *packages], cwd=workspace, env=workspace_env
        )
        assert res.returncode == 0, res.stdout + res.stderr

    return _install


@pytest.fixture
def run_cmd(workspace, workspace_env):
    """Run a command inside the task workspace's isolated environment."""

    def _run(*argv, cwd=None):
        return run(list(argv), cwd=cwd or workspace, env=workspace_env)

    return _run
