from pathlib import Path

import pytest

from doctest_ai.docs import DocsDir, NoDocs

PANDAS_PIN = "pandas==2.3.3"  # last 2.x line: saturated priors by design

# Version-matched snapshot fetched from the pandas repo at v2.3.3
# (doc/source/user_guide/{missing_data,groupby,io}.rst). The control's point
# is that even with a good-faith docs arm the delta stays ~0.
DOCS_DIR = Path(__file__).parent / "docs"

ARMS = ["none", "docs"]


@pytest.fixture
def docs_sources():
    return {"none": NoDocs(), "docs": DocsDir(str(DOCS_DIR))}
