# doctest-ai

Measure how much your documentation actually contributes to whether AI coding
agents succeed.

## What is doctest-ai?

Tools like Fern's Agent Score check whether agents can *read* your docs.
`doctest-ai` measures whether reading them makes agents *succeed*: it runs the
same tasks with and without your docs and reports the difference —

```
Docs Delta = success(with docs) − success(without docs)
```

— with honest confidence intervals, because agent runs are stochastic. If the
model's priors already cover your framework, the delta is ~0 no matter how
nice your docs are; if your last release broke every assistant's priors, the
delta is what your docs recover.

A *task* is a plain pytest test: you set up a workspace, hand the agent a
prompt, and verify the outcome deterministically — real code runs, objective
pass/fail, no LLM-judging-LLM.

```python
import doctest_ai


@doctest_ai.task(id="new-pipeline", arms=["none", "docs"])
def test_new_pipeline(agent, workspace, run_cmd):
    def check():
        res = run_cmd("kedro", "run")
        assert res.returncode == 0, res.stdout + res.stderr

    agent.solve("add a pipeline that ... and make `kedro run` succeed", check)
```

The plugin parametrizes every task across **docs arms** (which docs the agent
gets: none, an llms.txt, an MCP docs server, a mounted docs directory) and
**repetitions**, records one JSONL line per run, and `doctest-ai report`
renders the ablation with Wilson intervals and a paired-bootstrap delta.

## Prerequisites

- **Claude Code**: https://code.claude.com/docs/en/setup — headless runs bill
  at API rates; set `ANTHROPIC_API_KEY`.
- **uv**: https://docs.astral.sh/uv/getting-started/installation/

## Installation

```bash
uv pip install doctest-ai        # plain pytest API
uv pip install 'doctest-ai[bdd]' # + the legacy pytest-bdd/Gherkin adapter
```

## Quickstart

Declare the docs arms in your `conftest.py`:

```python
import pytest

from doctest_ai import DocsDir, LLMsTxt, MCPDocs, NoDocs


@pytest.fixture
def docs_sources():
    return {
        "none": NoDocs(),                       # baseline: priors only
        "llms-txt": LLMsTxt("https://example.dev/llms.txt"),
        "docs": DocsDir("path/to/docs-snapshot"),
    }
```

Write tasks (see `suites/` for the report-grade examples: Kedro 1.x,
Pandera's Narwhals backend, and a pandas control), then run the ablation:

```bash
pytest suites/kedro --doctest-reps=10 --doctest-artifact=results/kedro.jsonl
doctest-ai report results/kedro.jsonl
```

```
## Docs Delta (vs `none`)

### `mcp`: **+47pts** [+3pts, +90pts] (significant; 3 tasks, paired bootstrap)
```

Per-run transcripts land in `<artifact>.d/` for triaging failures.

## Configuration

Under `[tool.doctest-ai]` in `pyproject.toml`:

- `max_retries` — agentic retry loop: on a failed check, the error is fed
  back to the agent (distinguishes success@1 from success@N; both reported)
- `reps`, `arms`, `artifact` — defaults for the CLI options

Under `[tool.doctest-ai.claude-code]`: `model`, `allowed_tools`,
`disallowed_tools` (defaults disable `WebSearch`/`WebFetch` so the docs under
test are the only external channel), `max_turns`.

Swap the agent runtime by overriding the `agent_backend_factory` fixture —
Claude Code (via the official `claude-agent-sdk`) is the first backend, and
`FakeAgent` makes the whole harness testable without spending tokens.
