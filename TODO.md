# TODO — sentinel-dbt

## Goal
A thought experiment using the data is EuroSAT: 27,000 labeled satellite images in 10 class folders. The folders already give each image its class. Everything runs locally on DuckDB: clone → `pip install` → `dbt build`.

## Decisions
- **Warehouse:** DuckDB through `dbt-duckdb`
- **Tooling:** all installed in a project venv (`eurosat-dbt-venv/`, gitignored).
- **Data source:** Copernicus Data Space (CDSE) STAC catalog, ESA's official API. Catalog search needs no account. Metadata only; no image downloads.
- **API pull is cached as CSVs in the repo**, so the project runs without hitting the API.

## Plan: initial build (2026-10-08) -- up next

### 4. Models
- [x] **Sources:** a `locations` source with 12 tables in DuckDB (loaded from `data/raw/<location>.csv` by `load_raw.py`)
- [x] **Staging (scaffolded):** `stg__<location>` × 12, each selecting from `source('locations', '<location>')`
- [x] **Staging (filled in):** rename, cast types, unpack `statistics` JSON with the `unpack_statistics()` macro, and deduplicate to one row per capture (satellite + `acquired_at` + location; latest processing version, then lowest `nodata_pct`). Template in `stg__boston`, copied to all 12. 8,431 → 8,178 rows
- [x] **Macro `get_locations()`:** reads the `locations` seed with `run_query` and returns the rows as a list of dicts with keys `location_object_name`, `alias`, `filters`, `event_date`
- ~~**Macro `apply_scene_exclusions()`:** filters out `excluded_scenes` rows where `enabled`; a project var `exclude_flagged_scenes` (default true) turns it off~~ (dropped: no exclusion filter)
- [x] **Monster model `fct_location_daily_metrics`:** loops over `get_locations()`, builds one CTE per location (staging model + filter), unions them into one row per image (scene id, event date, location, cloud cover, nodata, `num_images = 1`) with a surrogate key. 8,178 rows
- [x] Layered config in `dbt_project.yml`: staging and intermediate = view, marts = table

### 5. Tests
- [x] **Generic:** `unique` / `not_null` on each `<location>_scene_id`, `scene_id` and `unique_image_id`; `accepted_values` on each staging model's tile and the monster model's `location_name`; one row per capture (`dbt_utils.unique_combination_of_columns` on satellite + `acquired_at` + location) in every staging model. Staging tests share YAML anchors (`models/staging/_locations__models.yml`); monster model in `models/marts/_marts__models.yml`. 119 tests, all pass
- [x] **Range checks (`dbt_expectations`):** `cloud_cover_pct` and `nodata_pct` between 0 and 100 (nodata allows the 2 nulls)
- ~~**Funnel order:** per region-month, each stage count ≤ the stage before it (usable ≤ clear ≤ mostly_clear ≤ processed)~~ (dropped)
- ~~**Drift guard:** monthly `captured` counts over a frozen window match a baseline seed~~ (dropped)
- ~~**Unit tests (dbt native):** the monster model on a few hand-built scenes (right metrics emitted per scene); the exclusion macro removes only enabled rows~~ (dropped)

### 6. Documentation
- [x] YAML descriptions for every model and column; `persist_docs` on the marts
- [x] Exposure `fetch_and_load_scripts` (`models/_exposures.yml`) on the `regions` seed, so it shows in the DAG
- [ ] README: what the project shows and why, setup steps, lineage screenshot from `dbt docs`. Done: title + purpose (from the write-up), write-up link, setup steps (venv, `pip install`, `dbt deps`). Left (optional): lineage diagram
- [x] Seed and source descriptions (`seeds/_seeds.yml`, `_locations__sources.yml`); overview page (`models/_overview.md`, adapted from finances-otovek)
- [x] Remove the Mac username (`root_path`) from `target/static_index.html` after each `dbt docs generate --static` (proposed: a script that generates + scrubs)
  - Plan (2026-10-12): add `scripts/generate_docs.py`: runs `dbt docs generate --static` with the venv's dbt, replaces the absolute project path in `target/static_index.html` with `eurosat-dbt`, and fails if the home path is still in the file. Run it and confirm the username is gone. Then add a README usage line: use this script instead of `dbt docs generate`
  - Done: 0 username hits. After each run, the file is moved by hand from `target/` to the repo root (`static_index.html`); the script itself still writes to `target/`
- [x] Rename eurosat → sentinel everywhere (approved 2026-10-12): folder and GitHub name `sentinel-dbt`, dbt project/profile `sentinel_dbt`, `sentinel.duckdb`, venv `sentinel-dbt-venv` (rebuilt), write-up links and docs filename; rebuild, regenerate docs to the repo root, refresh portfolio preview. Done: build 134 pass, docs have no `eurosat` and no username
- ~~Portfolio sync: `portfolio/scripts/sync-projects.sh` only copies `<repo>/dbt/target/static_index.html`; this project's docs are at `target/`, so the `eurosat-dbt-dbt-docs.html` links 404 until that's handled~~ (dropped: docs live at the repo root and get copied into the portfolio by hand, see step 8)
- [x] Portfolio write-up (`portfolio.ipynb`): Showcase trimmed to Data, Lineage, Staging, Monster model, Tests, Analysis; model and seed link to the dbt docs, scripts link to GitHub; outcome (14 metrics from 11 source models) in the front matter; blank lines before every list

### 7. Verify
- [x] Local preview of the portfolio page (`quarto preview`, port 4301) with the docs link working
- [x] Fresh clone → venv → `dbt deps` → `dbt build` passes with no errors (simulated in a scratch copy with no database: load_raw → deps → build = 134 pass; `dbt docs generate` works)
- ~~Turn off one exclusion and confirm the drift guard catches the count change~~ (dropped: no exclusion filter)

### 8. Publish
- [ ] Delete the empty last cell in `portfolio.ipynb`
- [ ] Commit (no Claude co-author lines)
- [ ] Create the public GitHub repo `autumngsmith/sentinel-dbt` and push (the write-up's script links and the site CI depend on this name)
- [ ] Docs on the live site: copy `static_index.html` to `portfolio/projects/sentinel-dbt-dbt-docs.html`, add `!projects/sentinel-dbt-dbt-docs.html` to the portfolio `.gitignore`, commit and push the portfolio repo
- [ ] Rebuild the site (`draft: false` is already set)
- [ ] Stop the local preview on port 4301


## Completed steps:

### 1. Setup
- [x] `git init`, `.gitignore` (venv, `target/`, `dbt_packages/`, `logs/`, `*.duckdb`)
- [x] Create the venv; `requirements.txt` with pinned `dbt-duckdb`
- [x] dbt skeleton; a `profiles.yml` inside the repo that points at a local `eurosat.duckdb`
- [x] `packages.yml`: `dbt_utils`, `dbt_expectations`
- [x] Swap `pillow` for `pystac-client` in `requirements.txt`

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

### 2.5 Raw data folder + load into DuckDB
- [x] Raw CSVs live in one folder that nothing in the project writes to except the fetch script: `data/raw/` (to be locked with a hook)
- [x] `scripts/load_raw.py`: reads each `<location>.csv` listed in `seeds/regions.csv` and creates a `locations.<location>` table in `eurosat.duckdb` (`create or replace`, explicit column types). Read-only on the CSVs
- [x] `models/staging/_locations__sources.yml`: a `locations` source pointing at the `locations` schema in the DuckDB database, 12 tables
- [x] Row counts match the CSVs (8,431 total); all 12 staging models build against the DuckDB tables. Full `dbt parse` blocked by the in-progress monster model (stray `endif`, line 23)
- [x] README usage: run `load_raw.py` before `dbt build` (the `.duckdb` file is gitignored, so a fresh clone rebuilds it from the CSVs)

### 3. Seeds
- [x] `regions.csv`: location key (matches `stg__<location>`), tile id, region name, country, climate note (12 tiles, mixing cloudy and sunny places)
- [x] `locations.csv` (renamed from `location_metrics.csv`): **drives the monster model.** One row per location: staging model (`stg__<location>`), alias (`<location>`), filter, event-date column (`acquired_at`). Adding a location = a seed row + a source table + a staging model
