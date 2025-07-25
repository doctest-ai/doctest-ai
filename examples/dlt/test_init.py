import subprocess
from pathlib import Path
from subprocess import PIPE, STDOUT

from pytest_bdd import given, parsers, scenario, then, when

from doctest_ai.sh_run import run

OK_EXIT_CODE = 0


@scenario("init.feature", "Create a new dlt project")
def test_init():
    pass


@given(parsers.parse("I have installed {package}"))
def install_package(request, package):
    """Install the specified package."""
    run(["uv", "pip", "install", package], check=True, env=request.env)


@when(
    "I ask Claude to create a dlt project with a single pipeline that loads data from the Pokemon API and stores it in a local directory",
)
def create_project(request, tmp_path):
    res = run(
        [
            "claude",
            "-p",
            "create a dlt project with a single pipeline that loads data from the Pokemon API and stores it in a local directory",
            "--mcp-config",
            str(Path(__file__).parent / "mcp-servers.json"),
            "--allowedTools",
            "Write",
            "--model",
            "claude-3-7-sonnet-20250219",
        ],
        cwd=tmp_path,
        env=request.env,
    )
    assert res.returncode == OK_EXIT_CODE, res

    def run_pipeline(tmp_path):
        return subprocess.run(
            ["python", "pokemon_pipeline.py"],
            stdout=PIPE,
            stderr=STDOUT,
            cwd=tmp_path,
            env=request.env,
        )

    max_iterations = 3
    for i in range(max_iterations):
        res = run_pipeline(tmp_path)
        if res.returncode == OK_EXIT_CODE:
            break

        res = subprocess.run(
            [
                "claude",
                "--continue",
                "-p",
                "fix this error",
                "--mcp-config",
                str(Path(__file__).parent / "mcp-servers.json"),
                "--allowedTools",
                "Bash(python pokemon_pipeline.py:*)",
                "Write",
                "--model",
                "claude-3-7-sonnet-20250219",
            ],
            input=res.stdout,
            cwd=tmp_path,
            env=request.env,
        )
        assert res.returncode == OK_EXIT_CODE, res


@then("the pipeline runs successfully")
def run_pipeline(request, tmp_path):
    res = run(["python", "pokemon_pipeline.py"], cwd=tmp_path, env=request.env)
    assert res.returncode == OK_EXIT_CODE, res
