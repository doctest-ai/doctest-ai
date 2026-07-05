"""Synthetic-internal ablation (the handoff's gate #1, simulated).

corax's names and conventions exist in no training set, so priors contribute
nothing; the vendored source is always readable (the honest internal-monorepo
condition). The measured delta is therefore exactly `code+docs − code-alone`:
what the docs add over what an agent can extract from the code itself.
"""

import json

import doctest_ai
from suites.internal_sim.conftest import ARMS


@doctest_ai.task(id="corax-daily-summary", arms=ARMS)
def test_daily_summary_strut(agent, corax_workspace, run_cmd):
    def check():
        res = run_cmd("python", "-m", "corax", "run", "daily-summary")
        assert res.returncode == 0, res.stdout + res.stderr
        payload = json.loads((corax_workspace / "daily-summary.out.json").read_text())
        assert payload.get("rows") == 3, payload

    agent.solve(
        "this project uses our internal corax platform library (vendored at "
        "./vendor/corax and already installed). Create a corax job named "
        "'daily-summary' that reads data.csv and records the number of data "
        "rows under the key 'rows', wired up so that "
        "`python -m corax run daily-summary` succeeds",
        check,
    )
