"""Pandera tasks — confident priors vs. the new Narwhals backend.

The classic-API task is the within-library control: models know pandas-era
pandera cold, so the docs delta should be ~0. The Narwhals-backend task holds
the library constant and varies only the subsystem's training-data coverage.
Two design constraints keep it honest: pandas is not installed (the confident
pandas-era solution cannot pass), and the verifier asserts the backend config
flag directly (the native polars backend — which models do know — cannot
pass either).
"""

import doctest_ai
from suites.pandera.conftest import (
    ARMS,
    PANDERA_CLASSIC_PIN,
    PANDERA_NARWHALS_PIN,
    SCHEMA_SPEC,
)

# Runs in the workspace venv; proves the Narwhals backend was actually
# enabled rather than trusting exit codes the native backend could produce.
NARWHALS_DRIVER = """
import validate

ok = validate.validate("good.csv")

import pandera.config

assert pandera.config.get_config_global().use_narwhals_backend, (
    "pandera's Narwhals backend is not enabled"
)
assert ok, "good.csv should validate"
assert not validate.validate("bad.csv"), "bad.csv should not validate"
"""


@doctest_ai.task(id="pandera-classic-schema", arms=ARMS)
def test_classic_dataframe_schema(agent, install, run_cmd, validation_data):
    """Within-library control: classic pandas-backed DataFrameSchema."""
    install(*PANDERA_CLASSIC_PIN)

    def check():
        res = run_cmd("python", "validate.py", "good.csv")
        assert res.returncode == 0, res.stdout + res.stderr
        res = run_cmd("python", "validate.py", "bad.csv")
        assert res.returncode != 0, "validator accepted invalid data"

    agent.solve(
        "write a script validate.py that loads the CSV file given as its "
        "first command-line argument into a pandas DataFrame and validates "
        f"it with a pandera schema; {SCHEMA_SPEC}. The script exits with "
        "code 0 when the data is valid and a nonzero code when it is not",
        check,
    )


@doctest_ai.task(id="pandera-narwhals-polars", arms=ARMS)
def test_narwhals_backend_polars(agent, install, run_cmd, validation_data):
    """The headline task: validate a polars LazyFrame via the Narwhals backend."""
    install(*PANDERA_NARWHALS_PIN)

    def check():
        res = run_cmd("python", "-c", NARWHALS_DRIVER)
        assert res.returncode == 0, res.stdout + res.stderr

    agent.solve(
        "write a python module validate.py that enables pandera's "
        "Narwhals-based validation backend process-wide and defines a "
        "function validate(path) that loads the CSV file at path into a "
        "polars LazyFrame and validates it with pandera, returning True when "
        f"the data is valid and False when it is not; {SCHEMA_SPEC}. Do not "
        "use pandas; it is not installed",
        check,
    )
