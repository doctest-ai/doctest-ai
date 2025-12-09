from doctest_ai.sh_run import run
from pytest_bdd import given, parsers, scenario, then

OK_EXIT_CODE = 0


@scenario("init.feature", "Create a new dlt project")
def test_init():
    pass


@given(parsers.parse("I have installed {package}"))
def install_package(request, package):
    """Install the specified package."""
    run(["uv", "pip", "install", package], check=True, env=request.env)


@then("the pipeline runs successfully")
def run_pipeline(request, tmp_path):
    res = run(["python", "pokemon_pipeline.py"], cwd=tmp_path, env=request.env)
    assert res.returncode == OK_EXIT_CODE, res
