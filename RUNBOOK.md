# v1 batch runbook — descoped, subscription-auth

How to produce the v1 Docs Delta numbers for roughly $0 incremental spend,
by running the descoped batch on Claude subscription auth over a few days.
Written 2026-07-06; intended to be executed after 2026-07-07.

**No AI assistant is needed to run any of this.** The batch is plain
`pytest` commands typed into a terminal. The only model involved is the
*agent under test* (`claude-sonnet-5`, pinned as `DEFAULT_MODEL` in
`src/doctest_ai/agent.py`) — keep it pinned so results stay comparable with
the 2026-07-05 signal check. Which model builds or babysits the harness is
irrelevant to the data.

## How subscription batches work now

Headless `claude` runs share the interactive session pool, so a batch dies
at the account usage limit with `AgentError: Claude Code run failed: ...`.
That used to poison the batch; it no longer does:

- A run killed by the runtime is recorded with `passed: null` — stats
  ignore it (it is not a task failure and never counts against an arm).
- Every command below carries `--doctest-resume`: re-running the *same
  command* skips every (task, arm, rep) that already has an outcome and
  retries the rest. Interrupted batches are idempotent to re-run.

So the loop is simply: start a suite, let it run until it finishes or the
limit kills it, wait for the limit window to reset, re-run the same
command. Repeat until the run count in the artifact is complete.

## Ground rules

1. Run from a plain terminal, **not** inside a Claude Code session.
   Anything else drawing on the subscription (including interactive Claude
   Code use) competes with the batch — schedule batches for hours/days you
   are not using Claude interactively.
2. `unset ANTHROPIC_API_KEY` first — an exported key would silently switch
   billing to API rates.
3. One suite per limit window (roughly: one per day) is a comfortable pace.
   `-n 2` (pytest-xdist) halves wall-clock; raise it only if limits allow.
4. `results/` is gitignored — back up the JSONL artifacts and `.d/`
   transcript dirs when the batch completes.
5. Do not upgrade the `claude` CLI, change `DEFAULT_MODEL`, or edit task
   prompts/verifiers mid-batch. If a task must change, discard that task's
   records and restart that task only.

## Day 0 — dress rehearsal (~$2 of subscription usage)

The corax sanctioned-registration task was tightened on 2026-07-06 (the
sanctioned team is now `ml-platform`, stated only in the docs) and has not
had a live run since. Re-vet it cheaply before spending real reps:

```bash
cd ~/github/doctest-ai/doctest-ai
unset ANTHROPIC_API_KEY

uv run pytest suites/internal_sim -k sanctioned --doctest-reps=1 \
  --doctest-artifact=results/v1-dress.jsonl --doctest-resume
```

Expected: `code-docs` passes; `code-alone` most likely fails (either path —
legacy `@corax.job` or a guessed team — fails review). **Read both
transcripts** in `results/v1-dress.jsonl.d/`: confirm the docs-arm agent
actually read the docs and chose `ml-platform`, and that the no-docs agent
failed for a convention reason, not a mechanics one. If anything looks off,
fix the task before Day 1.

## Days 1–4 — the batch (~360 runs total)

```bash
cd ~/github/doctest-ai/doctest-ai
unset ANTHROPIC_API_KEY

# Day 1 — corax, the headline (2 tasks x 2 arms x 15 reps = 60 runs)
uv run pytest suites/internal_sim --doctest-reps=15 -n 2 \
  --doctest-artifact=results/v1-corax.jsonl --doctest-resume

# Day 2 — pandera, headliner + within-library control (2 x 2 x 10 = 80)
uv run pytest suites/pandera --doctest-reps=10 -n 2 \
  --doctest-artifact=results/v1-pandera.jsonl --doctest-resume

# Day 3 — pandas control (2 x 2 x 10 = 80, cheapest runs)
uv run pytest suites/pandas_control --doctest-reps=10 -n 2 \
  --doctest-artifact=results/v1-pandas.jsonl --doctest-resume

# Day 4 — kedro, efficiency framing, reduced n (2 x 2 x 5 = 20)
uv run pytest suites/kedro --doctest-reps=5 -n 2 \
  --doctest-artifact=results/v1-kedro.jsonl --doctest-resume
```

After any interruption, re-run the day's command verbatim. To check
progress: `grep -c '"passed": true\|"passed": false' results/v1-<suite>.jsonl`
counts completed runs (`"passed": null` lines are limit-kills awaiting
retry and don't count).

API-rate equivalent for the whole batch is roughly **$65–140** (per-run
observed range $0.10–1.30 depending on task); on subscription that is $0
incremental — it just consumes plan limits.

## Rendering results

Suites use different baseline arm names, so deltas are per-suite:

```bash
uv run doctest-ai report results/v1-corax.jsonl --baseline=code-alone \
  --out results/v1-corax-report.md
uv run doctest-ai report results/v1-pandera.jsonl --out results/v1-pandera-report.md
uv run doctest-ai report results/v1-pandas.jsonl  --out results/v1-pandas-report.md
uv run doctest-ai report results/v1-kedro.jsonl   --out results/v1-kedro-report.md
```

Each report now includes the **Efficiency Delta** section (turns/cost among
passing runs, paired-bootstrap CIs) — that is the pre-registered primary
metric for the kedro suite and a secondary metric everywhere else.

Triage every failure you intend to publish by reading its transcript
(`<artifact>.jsonl.d/`) — the fabricated-verification incident is the
canonical reason.

## What this batch is, and is not

These runs execute with tool lockdown (`WebSearch`/`WebFetch` disallowed)
but **outside the Docker egress sandbox** — subscription OAuth is not
mounted into the sandbox, which requires an API key by design. The
2026-07-06 canary run confirmed the sandbox blocks arbitrary egress under
real agent behavior.

Treat this batch as the full dress rehearsal and the draft numbers: it
retires all task-design and variance risk for free. Before *publishing*,
decide between:

- **Re-run inside the sandbox with an API key** (~$65–140 real dollars,
  one clean spend with all design risk already retired) — the credibility
  gate the strategy doc committed to; or
- Publish from the subscription batch, disclosing tool-lockdown-only
  isolation and pointing at audited transcripts — weaker, cheaper, and
  honest only if every published failure was transcript-triaged.

The first option is the plan of record; the second is the fallback if the
draft numbers don't justify the spend.
