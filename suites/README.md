# Docs Delta report v1 task suites

Each suite measures `success(with docs) − success(without docs)` for one
target. Suites are plain pytest packages: `conftest.py` declares the docs
arms (`docs_sources` fixture) and setup helpers; each task is a
`@doctest_ai.task` test with a deterministic verifier.

| Suite | Target | Story |
|---|---|---|
| `kedro/` | Kedro 1.x | Stale priors: agents write 0.19-era code without docs |
| `pandera/` | Pandera + Narwhals backend | Confident library priors, zero subsystem priors; classic-API tasks are the within-library control |
| `pandas_control/` | pandas | Saturated priors: expected delta ≈ 0 (credibility control) |

## Running

```bash
# Signal check (go/no-go before spending the full budget): 1 task, few reps
pytest suites/kedro -k integration --doctest-reps=5 \
  --doctest-artifact=results/kedro-signal.jsonl

# Full ablation for one suite (parallel: workspaces are independent, and
# JSONL appends are line-atomic; scale -n to your rate limits)
pytest suites/kedro --doctest-reps=10 -n 4 \
  --doctest-artifact=results/kedro.jsonl

# Render the report
doctest-ai report results/kedro.jsonl
```

Requires `ANTHROPIC_API_KEY` (headless agent runs bill at API rates) and the
`claude` CLI installed. Transcripts land next to the artifact in
`<artifact>.d/` — read them when triaging any failure you intend to publish.

Subscription-auth batches are possible but need care: headless runs share
the interactive session pool, and hitting the limit mid-batch kills the
remaining runs with an `AgentError`. Runtime kills are recorded without an
outcome (`passed: null`, ignored by stats), and `--doctest-resume` makes
the same command idempotent to re-run after the limit window resets — see
`RUNBOOK.md` at the repo root for the full subscription batch procedure.
Budget roughly $0.15–1.30 per run at Sonnet API prices depending on task
size; a `max_turns` cap in `[tool.doctest-ai.claude-code]` bounds the
worst case.

## Vetting checklist (before any published number)

- [ ] Framework version pinned exactly; docs artifact matches that version
      (every `TODO(vet)` in the suite resolved).
- [ ] Verifier is airtight: passes on a known-good solution, fails on the
      known failure modes (including the "old API" solution).
- [ ] The no-docs arm fails *for the expected reason* — confirmed by reading
      transcripts, not just exit codes.
- [ ] Task is solvable with docs: at least one docs-arm run passes.
- [ ] Isolation: WebSearch/WebFetch disabled (default) and no MCP servers
      beyond the docs arm's own; Docker + egress allowlist before publishing.
