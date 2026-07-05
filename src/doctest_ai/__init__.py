"""doctest-ai: measure how much your docs contribute to AI agent success."""

import pytest

from doctest_ai.agent import (
    Agent,
    AgentResult,
    ClaudeAgent,
    ClaudeCLIAgent,
    FakeAgent,
)
from doctest_ai.docs import DocsDir, DocsSource, DocsSpec, LLMsTxt, MCPDocs, NoDocs

__all__ = [
    "Agent",
    "AgentResult",
    "ClaudeAgent",
    "ClaudeCLIAgent",
    "DocsDir",
    "DocsSource",
    "DocsSpec",
    "FakeAgent",
    "LLMsTxt",
    "MCPDocs",
    "NoDocs",
    "main",
    "task",
]


def task(id: str | None = None, arms: list[str] | None = None):  # noqa: A002
    """Mark a test as a doctest-ai task.

    The task is parametrized across docs arms and repetitions; it receives the
    ``agent`` (configured for the current arm) and ``workspace`` fixtures.
    """

    def decorator(fn):
        return pytest.mark.doctest_ai_task(task_id=id, arms=arms)(fn)

    return decorator


def main() -> int:
    from doctest_ai.report import main as report_main

    return report_main()
