import json
from pathlib import Path

import pytest

from doctest_ai.agent import (
    AgentResult,
    ClaudeCLIAgent,
    FakeAgent,
    _parse_cli_result,
)


def test_fake_agent_scripted_list(tmp_path):
    agent = FakeAgent(script=[AgentResult(success=False), AgentResult(success=True)])
    assert agent.run("first", cwd=tmp_path).success is False
    assert agent.run("second", cwd=tmp_path).success is True
    assert agent.calls == ["first", "second"]


def test_fake_agent_callable(tmp_path):
    agent = FakeAgent(script=lambda prompt, cwd: AgentResult(success="ok" in prompt))
    assert agent.run("ok?", cwd=tmp_path).success
    assert not agent.run("nope", cwd=tmp_path).success


def test_parse_cli_result_json():
    payload = {
        "type": "result",
        "is_error": False,
        "result": "done",
        "total_cost_usd": 0.42,
        "num_turns": 7,
        "duration_ms": 1234,
    }
    result = _parse_cli_result(json.dumps(payload))
    assert result.success
    assert result.output == "done"
    assert result.cost_usd == pytest.approx(0.42)
    assert result.num_turns == 7
    assert result.duration_ms == 1234


def test_parse_cli_result_non_json():
    result = _parse_cli_result("plain text output")
    assert result.success
    assert result.output == "plain text output"
    assert result.cost_usd is None


def test_cli_agent_build_command():
    agent = ClaudeCLIAgent(
        model="claude-sonnet-5",
        allowed_tools=["Write", "Edit"],
        mcp_config=Path("servers.json"),
    )
    cmd = agent._build_command("do it")
    assert cmd[:3] == ["claude", "--print", "do it"]
    assert "--allowedTools" in cmd and "Write,Edit" in cmd
    disallowed = cmd[cmd.index("--disallowedTools") + 1]
    assert "WebSearch" in disallowed and "WebFetch" in disallowed
    assert "--model" in cmd and "claude-sonnet-5" in cmd
    assert "--mcp-config" in cmd and "--strict-mcp-config" in cmd
