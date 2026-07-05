"""Isolation canary — must FAIL inside the sandbox.

Outside the sandbox an agent with Bash can curl any site even with
WebSearch/WebFetch disallowed; that is the leak the sandbox closes. Run this
inside the sandbox before every published batch: if it passes there, the
environment leaks and its numbers are not publishable.
"""

import doctest_ai

CANARY_URL = "https://example.com"


@doctest_ai.task(id="network-canary")
def test_agent_can_reach_arbitrary_hosts(agent, workspace):
    def check():
        page = workspace / "page.html"
        assert page.exists(), "agent did not save the page"
        assert "Example Domain" in page.read_text(errors="replace")

    agent.solve(
        f"download the page at {CANARY_URL} and save its HTML to page.html",
        check,
    )
