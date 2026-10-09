# TODO — eurosat-dbt

## Goal
A thought experiment using the data is EuroSAT: 27,000 labeled satellite images in 10 class folders. The folders already give each image its class. Everything runs locally on DuckDB: clone → `pip install` → `dbt build`.

## Decisions
- **Warehouse:** DuckDB through `dbt-duckdb`
- **Tooling:** all installed in a project venv (`eurosat-dbt-venv/`, gitignored).
- **Data source:** Copernicus Data Space (CDSE) STAC catalog, ESA's official API. Catalog search needs no account. Metadata only; no image downloads.
- **API pull is cached as CSVs in the repo**, so the project runs without hitting the API.

## Plan: initial build (2026-10-08) -- up next

### 2. Fetch script (`scripts/fetch_scenes.py`)
- [x] Confirm CDSE serves both the raw (`sentinel-2-l1c`) and processed (`sentinel-2-l2a`) collections
- [x] Read tiles from `seeds/regions.csv` (one list of tiles for the script and dbt); date range passed as arguments (default 2022-01-01 → 2026-09-30)
- [x] Search both collections per tile with a CQL2 filter on `grid:code` (`MGRS-<tile>`)
- [x] ~~Write one row per scene to `data/raw/scenes_l1c.csv` and `data/raw/scenes_l2a.csv`: scene id, tile, acquisition datetime, published/updated timestamps, processing version, cloud cover; L2A also gets the raw `statistics` JSON (L1C has none). Sorted output so re-runs give clean git diffs~~ (replaced by the per-location files below)
- [x] Write one CSV per location instead, `data/raw/<location>.csv` (e.g. `mexico_city.csv`), so each location is its own source table. **L2A only**: L1C dropped, since only 9 of ~8,400 captures lacked an L2A version. 12 files, 8,431 rows, identical to the earlier combined L2A pull
- [x] Commit the CSVs
- [x] Test on one tile, one year (30TVK: 2025 = 217 scenes per collection, 2022 = 150)
- [x] Check whether L1C and L2A counts ever differ (decides if the "processed" funnel stage stays) — 30TVK matched 1:1 in both 2022 and 2025
- [x] Document usage in the README

### 3. Seeds
- [x] `regions.csv`: location key (matches `stg__<location>`), tile id, region name, country, climate note (12 tiles, mixing cloudy and sunny places)
- [ ] `location_metrics.csv`: **drives the monster model.** One row per location: staging model (`stg__<location>`), alias (`<location>`), filter, event-date column (`acquired_at`). Adding a location = a seed row + a source table + a staging model

one model per place; as if each place is a source

when each place was passed over; transaction timestamp
alias - each place

### 4. Models
- [ ] **Sources:** a `locations` source with 12 tables, each pointing at its `data/raw/<location>.csv` as a DuckDB external source
- [x] **Staging (scaffolded):** `stg__<location>` × 12, each selecting from `source('locations', '<location>')`
- [ ] **Staging (filled in):** rename, cast types, unpack `statistics` JSON into columns (`nodata_pct`, cloud components)
- [ ] **Macro `get_locations()`:** reads `location_metrics` with `run_query` and returns the rows as a list of dicts (currently named `get_consultant_metrics` in `macros/get_locations.sql`, and returns `object_name` while the model reads `location_object_name`)
- [ ] **Macro `apply_scene_exclusions()`:** filters out `excluded_scenes` rows where `enabled`; a project var `exclude_flagged_scenes` (default true) turns it off
- [ ] **Monster model `fct_location_daily_metrics`:** loops over `get_locations()`, builds one CTE per location (staging model + filter + exclusions), unions them into one row per scene (scene id, tile, location, event date, `num_events = 1`) with a surrogate key
- [ ] Open: where the funnel stages (captured, clear, usable…) live now that the loop is over locations, e.g. flag columns on the monster model or the monthly mart
- [ ] **Mart `fct_region_monthly_funnel`:** one row per region × month × metric, summed from the monster model, ready for a funnel chart
- [ ] Layered config in `dbt_project.yml`: staging = view, intermediate and marts = table

### 5. Tests
- [ ] **Generic:** `unique` / `not_null` on the surrogate key and scene ids; `accepted_values` on metric name (kept in sync with the seed)
- [ ] **Range checks (`dbt_expectations`):** cloud cover and nodata between 0 and 100
- [ ] **Funnel order:** per region-month, each stage count ≤ the stage before it (usable ≤ clear ≤ mostly_clear ≤ processed)
- [ ] **Drift guard:** monthly `captured` counts over a frozen window match a baseline seed
- [ ] **Unit tests (dbt native):** the monster model on a few hand-built scenes (right metrics emitted per scene); the exclusion macro removes only enabled rows

### 6. Documentation
- [ ] YAML descriptions for every model and column; `persist_docs` on the marts
- [ ] `meta` on each mart (owner, source, grain)
- [ ] One exposure for the downstream consumer (portfolio page)
- [ ] README: what the project shows and why, setup steps, lineage screenshot from `dbt docs`

### 7. Verify
- [ ] Fresh clone → venv → `dbt deps` → `dbt build` passes with no errors
- [ ] Add a metric row to `funnel_metrics.csv` and confirm it shows up in the monster model with no SQL changes
- [ ] Turn off one exclusion and confirm the drift guard catches the count change


## Completed steps:

### 1. Setup
- [x] `git init`, `.gitignore` (venv, `target/`, `dbt_packages/`, `logs/`, `*.duckdb`)
- [x] Create the venv; `requirements.txt` with pinned `dbt-duckdb`
- [x] dbt skeleton; a `profiles.yml` inside the repo that points at a local `eurosat.duckdb`
- [x] `packages.yml`: `dbt_utils`, `dbt_expectations`
- [x] Swap `pillow` for `pystac-client` in `requirements.txt`