import os
import subprocess
import traceback
from pathlib import Path

import pytest
from pytest_bdd import exceptions, given, parsers, when
from pytest_bdd.scenario import _execute_step_function, get_step_function

from doctest_ai._config import ClaudeCodeSettings, Settings

from .sh_run import run

OK_EXIT_CODE = 0


def pytest_bdd_before_scenario(request, feature, scenario):
    _setup_minimal_env(request)

    # Store feature and scenario for _execute_then_step_functions later.
    request.feature = feature
    request.scenario = scenario


def _setup_context_with_venv(context, venv_dir):
    context.venv_dir = venv_dir
    # note the locations of some useful stuff
    # this is because exe resolution in subprocess doesn't respect a passed env
    if os.name == "posix":
        bin_dir = context.venv_dir / "bin"
    else:
        bin_dir = context.venv_dir / "Scripts"
    # TODO(deepyaman): Figure out whether noting locations is necessary.
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
    # Create venv
    tmp_path = request.getfixturevalue("tmp_path")
    run(["uv", "venv"], cwd=tmp_path, check=True)
    return tmp_path / ".venv"


def _setup_minimal_env(request):
    venv_dir = _create_new_venv(request)
    _setup_context_with_venv(request, venv_dir)


@pytest.fixture
def settings():
    """Return the Claude Code settings."""
    return ClaudeCodeSettings()


@given(
    "I have configured the following CLI options in Claude Code:",
    target_fixture="settings",
)
def _(datatable):
    """Configure the CLI options for Claude Code."""
    kwargs = {}
    for key, value in datatable:
        if key == "allowed_tools":
            kwargs[key] = value.split(",")
        else:
            kwargs[key] = value

    return ClaudeCodeSettings(**kwargs)


def _build_command(prompt, settings):
    cmd = ["claude", "--print", prompt]

    if settings.allowed_tools:
        cmd += ["--allowedTools", ",".join(settings.allowed_tools)]

    if settings.model:
        cmd += ["--model", settings.model]

    return cmd


def _execute_then_step_functions(request):
    """Execute the 'then' step functions registered for the scenario."""
    feature = request.feature
    scenario = request.scenario
    for step in scenario.steps:
        if step.type != "then":
            continue

        # https://github.com/pytest-dev/pytest-bdd/blob/8.1.0/src/pytest_bdd/scenario.py#L264-L273
        step_func_context = get_step_function(request=request, step=step)
        if step_func_context is None:
            exc = exceptions.StepDefinitionNotFoundError(
                f"Step definition is not found: {step}. "
                f'Line {step.line_number} in scenario "{scenario.name}" in the feature "{scenario.feature.filename}"'
            )
            request.config.hook.pytest_bdd_step_func_lookup_error(
                request=request, feature=feature, scenario=scenario, step=step, exception=exc  # noqa: E501
            )  # fmt: skip
            raise exc

        _execute_step_function(request, scenario, step, step_func_context)


@when(parsers.parse("I ask Claude to {prompt}"))
def _(request, tmp_path, prompt, settings):
    cmd = _build_command(prompt, settings)
    res = run(cmd, cwd=tmp_path, env=request.env)
    assert res.returncode == OK_EXIT_CODE, res

    if (max_iterations := Settings().max_iterations) is None:
        return

    for i in range(max_iterations):
        try:
            _execute_then_step_functions(request)
        except exceptions.StepDefinitionNotFoundError:
            raise
        except Exception:
            cmd = _build_command("fix this error", settings)
            exception = traceback.format_exc()
            res = subprocess.run(
                cmd, input=exception, cwd=tmp_path, text=True, env=request.env
            )
            assert res.returncode == OK_EXIT_CODE, res
        else:
            break
