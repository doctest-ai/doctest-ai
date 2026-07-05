from pathlib import Path

import pytest

from doctest_ai.docs import DocsDir, NoDocs

PANDAS_PIN = "pandas>=2.2,<3.0"  # TODO(vet): pin exactly for the report run

# TODO(vet): populate docs/ with a version-matched snapshot of the relevant
# pandas user-guide pages. The control's point is that even *with* docs the
# delta stays ~0 — the docs arm must still be a real, good-faith docs arm.
DOCS_DIR = Path(__file__).parent / "docs"

ARMS = ["none", "docs"]


@pytest.fixture
def docs_sources():
    return {"none": NoDocs(), "docs": DocsDir(str(DOCS_DIR))}
