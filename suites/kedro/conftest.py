import pytest

from doctest_ai.docs import MCPDocs, NoDocs

KEDRO_PIN = "kedro==1.5.0"
KEDRO_LLMS_TXT = "https://docs.kedro.org/en/1.5.0/llms.txt"  # version-matched

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
