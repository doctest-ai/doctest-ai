from pytest_bdd import scenarios, given, when, then, parsers

from .sh_run import run

OK_EXIT_CODE = 0

scenarios("new.feature")


@given(parsers.parse("I have installed {package}"))
def install_package(request, package):
    """Install the specified package."""
    run(["uv", "pip", "install", package], check=True, env=request.env)


@when(parsers.parse("I ask Claude to {prompt}"))
def create_project(request, tmp_path, prompt):
    res = run(
        [
            "claude",
            "-p",
            prompt,
            "--allowedTools",
            "Bash(kedro new:*)",
            "--model",
            "claude-3-7-sonnet-20250219",
        ],
        cwd=tmp_path,
        env=request.env,
    )
    assert res.returncode == OK_EXIT_CODE, res


@then("the expected project directories and files should be created")
def check_created_project_structure(tmp_path):
    """Check the subdirectories created by kedro new."""

    def is_created(name):
        """Check if path exists."""
        return (tmp_path / "project-dummy" / name).exists()

    for path in ("README.md", "src", "conf"):
        assert is_created(path)


@then("I can install the project-specific dependencies")
def install_dependencies(request, tmp_path):
    """Install the project-specific dependencies."""
    res = run(
        ["uv", "pip", "install", "-r", "requirements.txt"],
        cwd=tmp_path / "project-dummy",
        env=request.env,
    )
    assert res.returncode == OK_EXIT_CODE, res


@then(parsers.parse("the pipeline registry should {op}:"))
def check_pipeline_registry(request, tmp_path, op, datatable):
    """Check the pipelines created by kedro new."""
    assert op in ("contain", "not contain"), "Invalid step definition"
    res = run(
        ["kedro", "registry", "list"], cwd=tmp_path / "project-dummy", env=request.env
    )
    assert res.returncode == OK_EXIT_CODE, res
    for [name] in datatable:
        if op == "contain":
            assert name in res.stdout
        else:
            assert name not in res.stdout
