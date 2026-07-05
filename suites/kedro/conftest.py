import pytest

from doctest_ai.docs import MCPDocs, NoDocs

# TODO(vet): pin to the exact Kedro 1.x release the report runs against, and
# point the docs arm at the docs build for that same version.
KEDRO_PIN = "kedro>=1.0,<2.0"
KEDRO_LLMS_TXT = "https://docs.kedro.org/en/stable/llms.txt"

ARMS = ["none", "mcp"]


@pytest.fixture
def docs_sources():
    return {
        "none": NoDocs(),
        "mcp": MCPDocs(
            {
                "kedro-docs": {
                    "command": "uvx",
                    "args": [
                        "--from",
                        "mcpdoc",
                        "mcpdoc",
                        "--urls",
                        f"kedro:{KEDRO_LLMS_TXT}",
                    ],
                }
            }
        ),
    }
