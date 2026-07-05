"""Pandera tasks — confident priors vs. the new Narwhals backend.

The classic-API task is the within-library control: models know pandas-era
pandera cold, so the docs delta should be ~0. The Narwhals-backend tasks hold
the library constant and vary only the subsystem's training-data coverage —
and the workspace deliberately omits pandas, so a confident pandas-era
solution cannot pass.
"""

import doctest_ai
from suites.pandera.conftest import (
    ARMS,
    PANDERA_CLASSIC_PIN,
    PANDERA_NARWHALS_PIN,
    PROMPT_SPEC,
)


@doctest_ai.task(id="pandera-classic-schema", arms=ARMS)
def test_classic_dataframe_schema(agent, install, check_validator):
    """Within-library control: classic pandas-backed DataFrameSchema."""
    install(*PANDERA_CLASSIC_PIN)
    agent.solve(
        "write a script validate.py that loads a CSV file into a pandas "
        f"DataFrame and validates it with a pandera schema; {PROMPT_SPEC}",
        check_validator,
    )


@doctest_ai.task(id="pandera-narwhals-polars", arms=ARMS)
def test_narwhals_backend_polars(agent, install, check_validator):
    """The headline task: validate a polars frame via the Narwhals backend.

    pandas is not installed, so the pandas-era solution the model's priors
    suggest fails by construction.
    """
    install(*PANDERA_NARWHALS_PIN)
    agent.solve(
        "write a script validate.py that loads a CSV file into a polars "
        "LazyFrame and validates it with pandera's Narwhals-based backend "
        f"(do not use pandas; it is not installed); {PROMPT_SPEC}",
        check_validator,
    )
