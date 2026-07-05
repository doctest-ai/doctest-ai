"""Per-run records, the task-facing agent wrapper, and the JSONL recorder."""

from __future__ import annotations

import json
import time
import traceback
from dataclasses import asdict, dataclass, field
from pathlib import Path

from doctest_ai.agent import Agent, AgentResult

FIX_PROMPT = "fix this error"


@dataclass
class RunRecord:
    """One (task, arm, rep) execution — a single data point in the ablation."""

    task_id: str
    arm: str
    rep: int
    model: str | None = None
    attempts: int = 0
    first_attempt_passed: bool | None = None
    passed: bool | None = None
    cost_usd: float = 0.0
    num_turns: int = 0
    duration_s: float | None = None
    started_at: float = field(default_factory=time.time)
    error: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


class TaskAgent:
    """What a task function receives as the ``agent`` fixture.

    Wraps a backend with the docs-arm preamble, the workspace, telemetry
    accounting, and the agentic retry loop.
    """

    def __init__(
        self,
        backend: Agent,
        *,
        cwd: Path,
        env: dict[str, str] | None,
        record: RunRecord,
        preamble: str = "",
        max_retries: int = 0,
        transcript_dir: Path | None = None,
    ) -> None:
        self.backend = backend
        self.cwd = cwd
        self.env = env
        self.record = record
        self.preamble = preamble
        self.max_retries = max_retries
        self.transcript_dir = transcript_dir

    def run(self, prompt: str) -> AgentResult:
        """Run the agent once on ``prompt`` (with the docs-arm preamble)."""
        full_prompt = f"{prompt}\n\n{self.preamble}" if self.preamble else prompt
        result = self.backend.run(full_prompt, cwd=self.cwd, env=self.env)
        self.record.attempts += 1
        self.record.cost_usd += result.cost_usd or 0.0
        self.record.num_turns += result.num_turns or 0
        self._save_transcript(full_prompt, result)
        assert result.success, f"agent run failed: {result.output}"
        return result

    def solve(self, prompt: str, check, max_retries: int | None = None) -> None:
        """Run the agent, verify with ``check``, and retry on failure.

        ``check`` is a zero-argument callable that raises (usually via
        ``assert``) when the outcome is wrong. On failure the traceback is fed
        back to the agent up to ``max_retries`` times, mirroring how a human
        pastes an error back into the session. Distinguishes "failed on the
        first shot" (success@1) from "unrecoverable in N attempts" (success@N).
        """
        retries = self.max_retries if max_retries is None else max_retries
        self.run(prompt)
        last_exc: BaseException | None = None
        for attempt in range(retries + 1):
            try:
                check()
            except Exception as exc:
                if self.record.first_attempt_passed is None:
                    self.record.first_attempt_passed = False
                last_exc = exc
                if attempt == retries:
                    raise
                self.run(f"{FIX_PROMPT}\n\n{traceback.format_exc()}")
            else:
                if self.record.first_attempt_passed is None:
                    self.record.first_attempt_passed = attempt == 0
                return
        if last_exc is not None:  # pragma: no cover - defensive
            raise last_exc

    def _save_transcript(self, prompt: str, result: AgentResult) -> None:
        if self.transcript_dir is None:
            return
        self.transcript_dir.mkdir(parents=True, exist_ok=True)
        name = (
            f"{self.record.task_id}--{self.record.arm}"
            f"--rep{self.record.rep}--attempt{self.record.attempts}.txt"
        )
        path = self.transcript_dir / _slug(name)
        path.write_text(f"### PROMPT\n{prompt}\n\n### OUTPUT\n{result.output}\n")


def _slug(name: str) -> str:
    return "".join(c if c.isalnum() or c in "._-" else "-" for c in name)


class Recorder:
    """Appends run records to a JSONL artifact, one line per (task, arm, rep)."""

    def __init__(self, artifact: Path | None) -> None:
        self.artifact = artifact

    @property
    def transcript_dir(self) -> Path | None:
        if self.artifact is None:
            return None
        return self.artifact.with_suffix(self.artifact.suffix + ".d")

    def write(self, record: RunRecord) -> None:
        if self.artifact is None:
            return
        self.artifact.parent.mkdir(parents=True, exist_ok=True)
        with self.artifact.open("a") as f:
            f.write(json.dumps(record.to_dict()) + "\n")
