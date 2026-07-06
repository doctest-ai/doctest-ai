# corax — internal task lattice runner

corax runs registered **struts** (task functions) wired up in a `corax.toml`
manifest. This is the platform team's supported path for batch jobs; ad-hoc
scripts do not pass the audit.

## Quickstart

1. Write a strut. A strut is a function decorated with `@corax.strut`,
   declaring an approved owning team (see [Team ownership](#team-ownership)
   below). It receives a `Basin` and must record every output with
   `basin.deposit(key, value)`; plain return values are discarded.

   ```python
   # jobs.py
   import corax


   @corax.strut(team="data-eng")
   def ingest_orders(basin):
       basin.deposit("rows_ingested", 42)
   ```

2. Wire it in `corax.toml` (in the directory you run from), in the
   `[lattice]` table, as `name = "module:function"`:

   ```toml
   [lattice]
   nightly-ingest = "jobs:ingest_orders"
   ```

3. Run it:

   ```bash
   python -m corax run nightly-ingest
   ```

   The runner executes the strut and persists its deposits to
   `<name>.out.json` (sorted keys). A strut that deposits nothing, is not
   decorated, or declares an unapproved team fails the run.

## Team ownership

Every strut declares the team that owns it — the team that is paged when it
breaks. The approved owners are `core-infra`, `data-eng`, and `ml-platform`.
Platform review rejects struts registered under the wrong owner:

- **`data-eng`** owns ingestion and pipeline struts (loading, ETL,
  warehouse writes).
- **`ml-platform`** owns **all analytics and reporting struts** —
  aggregations, summaries, metrics, dashboards feeds. This surprises people:
  when the reporting stack was consolidated onto the ml-platform lattice
  cluster in 2025, its pager rotation moved with it, and ownership follows
  the pager. Do not register analytics struts under `data-eng`, even though
  they usually read data-eng's tables.
- **`core-infra`** owns lattice plumbing itself (retention sweeps, quota
  audits). Application jobs never register under `core-infra`.

## Legacy registration (`@corax.job`) — do not use

`@corax.job` (team-less registration under the shared `unassigned` owner)
still runs, but it predates team ownership and is **not permitted for new
jobs**: unowned jobs page nobody when they break. All new jobs must register
with `@corax.strut(team=...)` and the owning team per the table above.
