import shutil
from pathlib import Path

import pytest

from doctest_ai.docs import DocsDir, NoDocs

HERE = Path(__file__).parent
VENDOR = HERE / "vendor" / "corax"
DOCS_DIR = HERE / "docs"

ARMS = ["code-alone", "code-docs"]


@pytest.fixture
def docs_sources():
    return {"code-alone": NoDocs(), "code-docs": DocsDir(str(DOCS_DIR))}


@pytest.fixture
def corax_workspace(workspace, install):
    """Vendor corax into the workspace (readable source) and install it.

    Mirrors the internal-monorepo condition: the platform library's code is
    always visible; only the docs arm varies.
    """
    shutil.copytree(VENDOR, workspace / "vendor" / "corax")
    install(str(workspace / "vendor" / "corax"))
    (workspace / "data.csv").write_text("id,price\n1,10.0\n2,20.0\n3,30.0\n")
    return workspace
