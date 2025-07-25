import os
from pathlib import Path

from .sh_run import run


def pytest_bdd_before_scenario(request, feature, scenario):
    _setup_minimal_env(request)


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
