import pytest

from doctest_ai._config import ClaudeCodeSettings
from doctest_ai.docs import MCPDocs, NoDocs

KEDRO_PIN = "kedro==1.5.0"
KEDRO_LLMS_TXT = "https://docs.kedro.org/en/1.5.0/llms.txt"  # version-matched

ARMS = ["none", "mcp"]

# Pre-registered turn budget (2026-07-06, before the full batch): generous
# relative to every observed passing run (max 46 turns in the signal check)
# so it should never bind on a healthy run in either arm — it exists to cap
# the cost of pathological tails, not to manufacture a pass-rate delta.
MAX_TURNS = 60


@pytest.fixture
def settings():
    return ClaudeCodeSettings(max_turns=MAX_TURNS)


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
