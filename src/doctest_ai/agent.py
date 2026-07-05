"""Agent protocol and backends.

doctest-ai measures how much docs contribute to whether *agents* succeed at
tasks, so the agent itself is a swappable input. The protocol is deliberately
tiny; backends wrap real agent runtimes (Claude Code via the official
claude-agent-sdk, or the ``claude`` CLI) or fake ones for tests.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Protocol, runtime_checkable

DEFAULT_MODEL = "claude-sonnet-5"

# The agent should be fully capable locally — the ablation varies only the
# docs, so capability must not be the binding constraint...
DEFAULT_ALLOWED_TOOLS = ["Bash", "Edit", "Glob", "Grep", "Read", "Write"]

# ...but headless runs must never fall back to general web access; the docs
# under test are the only external information channel.
DEFAULT_DISALLOWED_TOOLS = ["WebSearch", "WebFetch"]


class AgentError(RuntimeError):
    """The agent runtime itself failed (nonzero exit, transport error)."""


@dataclass
class AgentResult:
    """Outcome of a single agent invocation."""

    success: bool
    output: str = ""
    cost_usd: float | None = None
    num_turns: int | None = None
    duration_ms: int | None = None
    raw: Any = None


@runtime_checkable
class Agent(Protocol):
    """Anything that can take a prompt and act on a working directory."""

    def run(
        self, prompt: str, *, cwd: Path, env: dict[str, str] | None = None
    ) -> AgentResult: ...


@dataclass
class ClaudeAgent:
    """Claude Code backend via the official ``claude-agent-sdk`` package.

    Headless/SDK usage bills at API rates (set ``ANTHROPIC_API_KEY``); do not
    assume subscription-subsidized runs.
    """

    model: str | None = DEFAULT_MODEL
    allowed_tools: list[str] = field(default_factory=list)
    disallowed_tools: list[str] = field(
        default_factory=lambda: list(DEFAULT_DISALLOWED_TOOLS)
    )
    mcp_servers: dict[str, Any] = field(default_factory=dict)
    system_prompt: str | None = None
    max_turns: int | None = None

    def run(
        self, prompt: str, *, cwd: Path, env: dict[str, str] | None = None
    ) -> AgentResult:
        import anyio
        from claude_agent_sdk import (
            AssistantMessage,
            ClaudeAgentOptions,
            ResultMessage,
            TextBlock,
            query,
        )

        options = ClaudeAgentOptions(
            model=self.model,
            allowed_tools=list(self.allowed_tools),
            disallowed_tools=list(self.disallowed_tools),
            mcp_servers=dict(self.mcp_servers),
            system_prompt=self.system_prompt,
            max_turns=self.max_turns,
            cwd=str(cwd),
            env=dict(env) if env else {},
        )

        async def _run() -> tuple[list[str], Any]:
            texts: list[str] = []
            result = None
            async for message in query(prompt=prompt, options=options):
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            texts.append(block.text)
                elif isinstance(message, ResultMessage):
                    result = message
            return texts, result

        try:
            texts, result = anyio.run(_run)
        except Exception as exc:
            # Surfaces CLI-side failures (auth, usage limits, crashes) with a
            # actionable label; subscription limits are the common culprit on
            # unkeyed runs.
            raise AgentError(f"Claude Code run failed: {exc}") from exc
        if result is None:
            raise AgentError("claude-agent-sdk returned no result message")
        return AgentResult(
            success=not result.is_error,
            output="\n".join(texts),
            cost_usd=result.total_cost_usd,
            num_turns=result.num_turns,
            duration_ms=result.duration_ms,
            raw=result,
        )


@dataclass
class ClaudeCLIAgent:
    """Fallback backend shelling out to ``claude --print --output-format json``."""

    model: str | None = DEFAULT_MODEL
    allowed_tools: list[str] = field(default_factory=list)
    disallowed_tools: list[str] = field(
        default_factory=lambda: list(DEFAULT_DISALLOWED_TOOLS)
    )
    mcp_config: Path | None = None

    def _build_command(self, prompt: str) -> list[str]:
        cmd = ["claude", "--print", prompt, "--output-format", "json"]
        if self.allowed_tools:
            cmd += ["--allowedTools", ",".join(self.allowed_tools)]
        if self.disallowed_tools:
            cmd += ["--disallowedTools", ",".join(self.disallowed_tools)]
        if self.model:
            cmd += ["--model", self.model]
        if self.mcp_config:
            cmd += ["--mcp-config", str(self.mcp_config), "--strict-mcp-config"]
        return cmd

    def run(
        self, prompt: str, *, cwd: Path, env: dict[str, str] | None = None
    ) -> AgentResult:
        res = subprocess.run(  # noqa: S603
            self._build_command(prompt),
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
        )
        if res.returncode != 0:
            raise AgentError(
                f"claude exited with {res.returncode}: {res.stderr or res.stdout}"
            )
        return _parse_cli_result(res.stdout)


def _parse_cli_result(stdout: str) -> AgentResult:
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return AgentResult(success=True, output=stdout)
    return AgentResult(
        success=not payload.get("is_error", False),
        output=payload.get("result", ""),
        cost_usd=payload.get("total_cost_usd"),
        num_turns=payload.get("num_turns"),
        duration_ms=payload.get("duration_ms"),
        raw=payload,
    )


@dataclass
class FakeAgent:
    """Scripted agent for tokenless tests.

    ``script`` is either a list of results consumed one per call, or a
    callable ``(prompt, cwd) -> AgentResult`` for behavior that depends on the
    prompt (e.g. succeeding only on a "fix this error" retry).
    """

    script: list[AgentResult] | Callable[[str, Path], AgentResult] | None = None
    calls: list[str] = field(default_factory=list)

    def run(
        self, prompt: str, *, cwd: Path, env: dict[str, str] | None = None
    ) -> AgentResult:
        self.calls.append(prompt)
        if callable(self.script):
            return self.script(prompt, cwd)
        if self.script:
            return self.script.pop(0)
        return AgentResult(success=True, output="ok", cost_usd=0.0)
