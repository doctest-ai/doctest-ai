"""Optional pytest-bdd adapter (the original Gherkin front door).

Registered as a plugin by ``doctest_ai.plugin`` only when pytest-bdd is
installed. New suites should prefer the plain ``@doctest_ai.task`` API; this
adapter keeps existing ``.feature``-based suites working.
"""

from __future__ import annotations

import logging
import subprocess
import traceback

from pytest_bdd import exceptions, given, parsers, when
from pytest_bdd.scenario import _execute_step_function, get_step_function

from doctest_ai._config import ClaudeCodeSettings, Settings
from doctest_ai.plugin import _setup_minimal_env
from doctest_ai.sh_run import run

OK_EXIT_CODE = 0

logger = logging.getLogger(__name__)


def pytest_bdd_before_scenario(request, feature, scenario):
    _setup_minimal_env(request)

    # Store feature and scenario for _execute_then_step_functions later.
    request.feature = feature
    request.scenario = scenario


@given(
    "I have configured the following CLI options in Claude Code:",
    target_fixture="settings",
)
def _(datatable):
    """Configure the CLI options for Claude Code."""
    kwargs = {}
    for key, value in datatable:
        if key in ("allowed_tools", "disallowed_tools"):
            kwargs[key] = value.split(",")
        else:
            kwargs[key] = value

    return ClaudeCodeSettings(**kwargs)


def _build_command(prompt, settings):
    cmd = ["claude", "--print", prompt]

    if settings.allowed_tools:
        cmd += ["--allowedTools", ",".join(settings.allowed_tools)]

    if settings.disallowed_tools:
        cmd += ["--disallowedTools", ",".join(settings.disallowed_tools)]

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

    if (max_retries := Settings().max_retries) is None:
        return

    for i in range(max_retries):
        try:
            _execute_then_step_functions(request)
        except exceptions.StepDefinitionNotFoundError:
            raise
        except Exception:
            cmd = _build_command("fix this error", settings)
            exception = traceback.format_exc()
            logger.info(
                "Error executing 'then' step, retrying... (attempt %s of %s)",
                i + 1,
                max_retries,
            )
            res = subprocess.run(
                cmd, input=exception, cwd=tmp_path, text=True, env=request.env
            )
            assert res.returncode == OK_EXIT_CODE, res
        else:
            break
