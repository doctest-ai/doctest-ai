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


# Both registration paths *work*; only the docs say which one is sanctioned
# (@corax.strut with the owning team). The sanctioned owner for analytics is
# ml-platform for an org-historical reason stated only in the docs — the
# semantically natural guess (data-eng) is a valid team that fails review, so
# a code-alone pass cannot happen by lucky inference. This is the knowledge
# source cannot encode: the code channel sees two equally valid APIs and
# three equally valid teams.
#
# Assertion messages deliberately do not name the sanctioned team: on
# retry-enabled runs the traceback is fed back to the agent, and leaking the
# answer there would let the no-docs arm recover without the docs.
CONVENTION_DRIVER = """
import importlib
import sys
import tomllib
from pathlib import Path

target = tomllib.loads(Path("corax.toml").read_text())["lattice"]["weekly-totals"]
module_name, _, func_name = target.partition(":")
sys.path.insert(0, ".")
fn = getattr(importlib.import_module(module_name), func_name)
meta = fn.__corax_strut__
assert meta["via"] == "strut", (
    "platform review: legacy @corax.job registration is not permitted for new jobs"
)
assert meta["team"] == "ml-platform", (
    f"platform review: {meta['team']!r} is not the owning team for analytics "
    "struts; see the platform docs for team ownership"
)
"""


@doctest_ai.task(id="corax-sanctioned-registration", arms=ARMS)
def test_weekly_totals_follows_conventions(agent, corax_workspace, run_cmd):
    def check():
        res = run_cmd("python", "-m", "corax", "run", "weekly-totals")
        assert res.returncode == 0, res.stdout + res.stderr
        payload = json.loads((corax_workspace / "weekly-totals.out.json").read_text())
        assert payload.get("total_price") == 60.0, payload
        res = run_cmd("python", "-c", CONVENTION_DRIVER)
        assert res.returncode == 0, res.stdout + res.stderr

    agent.solve(
        "this project uses our internal corax platform library (vendored at "
        "./vendor/corax and already installed). Create a corax job named "
        "'weekly-totals' that reads data.csv and records the total of the "
        "price column under the key 'total_price', wired up so that "
        "`python -m corax run weekly-totals` succeeds and the job passes "
        "platform review",
        check,
    )
