"""corax — the internal task lattice runner.

Synthetic stand-in for a proprietary platform library: the API names and
conventions are deliberately absent from any model's training data, so the
only information channels are this source and (in the docs arm) the docs.
"""

from __future__ import annotations

APPROVED_TEAMS = frozenset({"core-infra", "data-eng", "ml-platform"})


class Basin:
    """Collects a strut's outputs; the runner persists them after the run."""

    def __init__(self) -> None:
        self._deposits: dict[str, object] = {}

    def deposit(self, key: str, value: object) -> None:
        if not isinstance(key, str) or not key:
            raise ValueError("deposit key must be a non-empty string")
        self._deposits[key] = value


def strut(*, team: str):
    """Register a function as a runnable strut owned by ``team``."""

    def wrap(fn):
        fn.__corax_strut__ = {"team": team, "via": "strut"}
        return fn

    return wrap


def job(fn):
    """Register a function as a runnable job.

    Team-less registration; runs under the shared ``unassigned`` owner.
    """
    fn.__corax_strut__ = {"team": "unassigned", "via": "job"}
    return fn
