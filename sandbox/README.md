# Sandbox — network isolation for published numbers

Tool lockdown (`WebSearch`/`WebFetch` disallowed) is enough while developing,
but it is not airtight: an agent with `Bash` can `curl` any docs site, which
would contaminate the no-docs arm. Before publishing numbers, run the
ablation inside this sandbox: the runner container sits on an internal-only
Docker network whose sole egress path is a deny-by-default HTTP proxy that
allows exactly the hosts a clean run needs.

```
runner (internal network, no direct egress)
   └── HTTPS_PROXY ──> tinyproxy (deny-by-default allowlist) ──> internet
```

Baseline allowlist: `api.anthropic.com` (the model API), `pypi.org` +
`files.pythonhosted.org` (task setup installs pinned packages). Docs-arm
hosts (e.g. `docs.kedro.org` for the Kedro MCP arm) are added per run via
`EXTRA_ALLOWED_HOSTS` — and must NOT be set on no-docs-arm runs.

## Usage

```bash
cd sandbox

# No-docs arm: nothing beyond the baseline allowlist
ANTHROPIC_API_KEY=... docker compose run --rm runner \
  pytest suites/pandera -k narwhals --docs-arm=none \
  --doctest-reps=10 --doctest-artifact=results/pandera-none.jsonl

# Docs arm that needs a remote docs host (Kedro MCP):
ANTHROPIC_API_KEY=... EXTRA_ALLOWED_HOSTS=docs.kedro.org \
  docker compose run --rm runner \
  pytest suites/kedro --docs-arm=mcp \
  --doctest-reps=10 --doctest-artifact=results/kedro-mcp.jsonl
```

Inside the sandbox the agent authenticates with `ANTHROPIC_API_KEY` (API
billing) — subscription OAuth credentials are not mounted.

## Verifying isolation (the canary)

`suites/canary` asks the agent to download a page from a host that is not on
the allowlist. Outside the sandbox this passes (Bash + curl); inside it must
fail:

```bash
# Outside: expected to PASS (which is exactly the leak the sandbox closes)
pytest suites/canary --docs-arm=none

# Inside: expected to FAIL — run this before every published batch
docker compose run --rm runner pytest suites/canary --docs-arm=none
```

If the canary passes inside the sandbox, the numbers from that environment
are not publishable.
