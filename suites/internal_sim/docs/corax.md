# corax — internal task lattice runner

corax runs registered **struts** (task functions) wired up in a `corax.toml`
manifest. This is the platform team's supported path for batch jobs; ad-hoc
scripts do not pass the audit.

## Quickstart

1. Write a strut. A strut is a function decorated with `@corax.strut`,
   declaring an approved owning team (`core-infra`, `data-eng`, or
   `ml-platform` — analytics jobs belong to `data-eng`). It receives a
   `Basin` and must record every output with `basin.deposit(key, value)`;
   plain return values are discarded.

   ```python
   # jobs.py
   import corax


   @corax.strut(team="data-eng")
   def row_report(basin):
       basin.deposit("rows", 42)
   ```

2. Wire it in `corax.toml` (in the directory you run from), in the
   `[lattice]` table, as `name = "module:function"`:

   ```toml
   [lattice]
   daily-summary = "jobs:row_report"
   ```

3. Run it:

   ```bash
   python -m corax run daily-summary
   ```

   The runner executes the strut and persists its deposits to
   `<name>.out.json` (sorted keys). A strut that deposits nothing, is not
   decorated, or declares an unapproved team fails the run.

## Legacy registration (`@corax.job`) — do not use

`@corax.job` (team-less registration under the shared `unassigned` owner)
still runs, but it predates team ownership and is **not permitted for new
jobs**: unowned jobs page nobody when they break. All new jobs must register
with `@corax.strut(team=...)` and the owning team. Analytics and reporting
jobs belong to `data-eng`.
