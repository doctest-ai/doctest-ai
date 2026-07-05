"""pandas control tasks — saturated priors, expected docs delta ~= 0.

If the metric is honest, these tasks pass at the same (high) rate with and
without docs. A nonzero delta here means the harness, not the docs, is doing
something — which is exactly what the control exists to catch.
"""

import csv

import doctest_ai
from suites.pandas_control.conftest import ARMS, PANDAS_PIN

DATA_CSV = "id,price\n1,10.0\n2,\n3,30.0\n"
SALES_CSV = "category,amount\nb,2.0\na,1.0\nb,3.0\na,4.0\n"


@doctest_ai.task(id="pandas-fillna-median", arms=ARMS)
def test_fillna_median(agent, workspace, install, run_cmd):
    install(PANDAS_PIN)
    (workspace / "data.csv").write_text(DATA_CSV)

    def check():
        res = run_cmd("python", "clean.py")
        assert res.returncode == 0, res.stdout + res.stderr
        with (workspace / "cleaned.csv").open() as f:
            rows = {row["id"]: row["price"] for row in csv.DictReader(f)}
        assert float(rows["2"]) == 20.0  # median of 10.0 and 30.0
        assert float(rows["1"]) == 10.0 and float(rows["3"]) == 30.0

    agent.solve(
        "write a script clean.py that reads data.csv, fills missing values "
        "in the 'price' column with that column's median, and writes the "
        "result to cleaned.csv with the same columns",
        check,
    )


@doctest_ai.task(id="pandas-groupby-totals", arms=ARMS)
def test_groupby_totals(agent, workspace, install, run_cmd):
    install(PANDAS_PIN)
    (workspace / "sales.csv").write_text(SALES_CSV)

    def check():
        res = run_cmd("python", "totals.py")
        assert res.returncode == 0, res.stdout + res.stderr
        with (workspace / "totals.csv").open() as f:
            rows = [(row["category"], float(row["total"])) for row in csv.DictReader(f)]
        assert rows == [("a", 5.0), ("b", 5.0)]

    agent.solve(
        "write a script totals.py that reads sales.csv (columns: category, "
        "amount), computes the total amount per category, and writes "
        "totals.csv with columns 'category' and 'total', sorted by category",
        check,
    )
