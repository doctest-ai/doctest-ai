"""``python -m corax run <name>`` — execute a strut wired in corax.toml."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
import tomllib
from pathlib import Path

from corax import APPROVED_TEAMS, Basin


def _fail(message: str) -> None:
    print(f"corax: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser(prog="corax")
    parser.add_argument("command", choices=["run"])
    parser.add_argument("name")
    args = parser.parse_args()

    config = Path("corax.toml")
    if not config.is_file():
        _fail("corax.toml not found in the working directory")
    lattice = tomllib.loads(config.read_text()).get("lattice", {})
    target = lattice.get(args.name)
    if not target:
        _fail(f"no strut named {args.name!r} in the [lattice] table")

    module_name, _, func_name = target.partition(":")
    sys.path.insert(0, str(Path.cwd()))
    try:
        fn = getattr(importlib.import_module(module_name), func_name)
    except (ImportError, AttributeError) as exc:
        _fail(f"cannot load {target!r}: {exc}")

    meta = getattr(fn, "__corax_strut__", None)
    if meta is None:
        _fail(f"{target!r} is not a registered strut (missing @corax.strut)")
    if meta["via"] != "job" and meta["team"] not in APPROVED_TEAMS:
        _fail(f"team {meta['team']!r} is not an approved owner")

    basin = Basin()
    fn(basin)
    if not basin._deposits:
        _fail("strut completed without depositing any outputs")
    out = Path(f"{args.name}.out.json")
    out.write_text(json.dumps(basin._deposits, sort_keys=True))
    print(f"corax: wrote {out}")


if __name__ == "__main__":
    main()
