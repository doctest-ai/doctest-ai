from pathlib import Path

import pytest

from doctest_ai.docs import DocsDir, NoDocs

# TODO(vet): pin the exact pandera release that ships the experimental
# Narwhals-based backend, and the matching polars/narwhals versions.
PANDERA_CLASSIC_PIN = ("pandera", "pandas")
PANDERA_NARWHALS_PIN = ("pandera[polars]", "polars", "narwhals")

# TODO(vet): populate docs/ with a version-matched snapshot of the pandera
# docs (at minimum the DataFrameSchema guide and the Narwhals backend guide).
DOCS_DIR = Path(__file__).parent / "docs"

ARMS = ["none", "docs"]

GOOD_CSV = "id,price\n1,10.0\n2,20.0\n3,30.0\n"
BAD_CSV = "id,price\n1,10.0\n1,-5.0\n3,30.0\n"  # duplicate id, negative price

PROMPT_SPEC = (
    "the schema must require: column 'id' containing unique integers, and "
    "column 'price' containing floats strictly greater than 0. The script "
    "takes the CSV path as its first command-line argument and exits with "
    "code 0 when the data is valid and a nonzero code when it is not"
)


@pytest.fixture
def docs_sources():
    return {"none": NoDocs(), "docs": DocsDir(str(DOCS_DIR))}


@pytest.fixture
def validation_data(workspace):
    (workspace / "good.csv").write_text(GOOD_CSV)
    (workspace / "bad.csv").write_text(BAD_CSV)


@pytest.fixture
def check_validator(run_cmd, validation_data):
    """The verifier both pandera tasks share: exit 0 on good, nonzero on bad."""

    def check():
        res = run_cmd("python", "validate.py", "good.csv")
        assert res.returncode == 0, res.stdout + res.stderr
        res = run_cmd("python", "validate.py", "bad.csv")
        assert res.returncode != 0, "validator accepted invalid data"

    return check
