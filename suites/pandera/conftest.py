from pathlib import Path

import pytest

from doctest_ai.docs import DocsDir, NoDocs

PANDERA_VERSION = "0.32.1"  # first release line with the Narwhals backend (0.32.0)
PANDERA_CLASSIC_PIN = (f"pandera=={PANDERA_VERSION}", "pandas==2.3.3")
PANDERA_NARWHALS_PIN = (
    f"pandera[narwhals,polars]=={PANDERA_VERSION}",
    "polars==1.42.1",
    "narwhals==2.23.0",
)

# Version-matched snapshot fetched from the pandera repo at v0.32.1
# (docs/source/{narwhals_backend,dataframe_schemas,polars}.md).
DOCS_DIR = Path(__file__).parent / "docs"

ARMS = ["none", "docs"]

GOOD_CSV = "id,price\n1,10.0\n2,20.0\n3,30.0\n"
BAD_CSV = "id,price\n1,10.0\n1,-5.0\n3,30.0\n"  # duplicate id, negative price

SCHEMA_SPEC = (
    "the schema must require: column 'id' containing unique integers, and "
    "column 'price' containing floats strictly greater than 0"
)


@pytest.fixture
def docs_sources():
    return {"none": NoDocs(), "docs": DocsDir(str(DOCS_DIR))}


@pytest.fixture
def validation_data(workspace):
    (workspace / "good.csv").write_text(GOOD_CSV)
    (workspace / "bad.csv").write_text(BAD_CSV)
