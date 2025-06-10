from pytest_bdd import scenario, when, then

from .sh_run import run

OK_EXIT_CODE = 0


@scenario("new.feature", "Create a new kedro project without example code")
def test_new():
    pass


@when(
    'I ask Claude to create a new kedro project named "Project Dummy" without example code'
)
def create_project(tmp_path):
    res = run(
        [
            "claude",
            "-p",
            'create a new kedro project named "Project Dummy" without example code',
            "--allowedTools",
            "Bash(kedro new:*)",
        ],
        cwd=tmp_path,
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
