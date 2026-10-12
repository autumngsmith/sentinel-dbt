This project uses the **catalog of Sentinel-2 satellite photos**: a list describing each photo, not the photos themselves.

## The basics
- **Sentinel-2** is a set of European Space Agency (ESA) satellites that photograph all of Earth's land every few days. 
- **Scene:** one photo of one area at one moment. This is the main thing being counted.
- **Tile:** Earth is divided into a fixed grid of squares about 110 km across, each with a code like `30TVK`. Every scene belongs to one tile. A "region" in this project is a tile that has been selected and given a name.
- **Level-2A (L2A):** the processing level used here: each photo after ESA corrects it for the atmosphere and runs its analysis on it (cloud detection and so on).
- **Catalog:** ESA publishes a searchable list with one entry per scene: when it was taken, which tile, and summary stats ESA calculated. That list is the project's data. No photos are downloaded.
- **One source per location:** each location is stored as its own table, simulating a separately ingested source (like one data feed per client or store). The monster model unions them into one.

## What one row looks like
This is a real scene pulled from the catalog during setup:

| field | value | meaning |
|---|---|---|
| scene id | `S2C_MSIL2A_20261009T005651_N0513_R088_T59WNU_…` | Satellite S2C, Level-2A, taken 2026-10-09 at 00:56 UTC, tile 59WNU |
| tile | `59WNU` | Which grid square (this one is in far-eastern Russia) |
| acquired | 2026-10-09 00:56 | When the photo was taken |
| processing version | 05.13 | Which version of ESA's software processed it |
| cloud cover | 100% | Completely clouded over |
| nodata | 77.7% | Most of the tile wasn't covered; the satellite's path only clipped the edge |
| high-prob. clouds, water, vegetation… | various % | ESA's breakdown of what's in the picture |

That scene would not count as usable: it's neither clear nor full coverage.

## How the models fit together
- **Sources:** one DuckDB table per location (`locations.<location>`), loaded from `data/raw/<location>.csv`.
- **Staging:** `stg__<location>` unpacks the statistics JSON and deduplicates to one row per capture.
- **Monster model:** `fct_location_daily_metrics` unions every location into one row per image. Each row of `seeds/locations.csv` is one location, so adding a location is a seed row, not new model code.

## Scale
12 tiles from 2022-01-01 to 2026-09-30: **8,431 rows** raw, **8,178** after deduplication.

## Usage
The fetched CSVs are committed in `data/raw/` and are never edited by hand. dbt reads from DuckDB, not the CSVs, so load them first:

```bash
source eurosat-dbt-venv/bin/activate
python scripts/load_raw.py   # creates locations.<location> tables in eurosat.duckdb
dbt build
```

To re-fetch the CSVs from the API:

```bash
python scripts/fetch_scenes.py                                      # all locations in seeds/regions.csv, 2022-01-01 → 2026-09-30
python scripts/fetch_scenes.py --start 2025-01-01 --end 2025-12-31  # custom date range
```

Each location in `seeds/regions.csv` gets its own file, `data/raw/<location>.csv`. To add a location, add a row with its `location` key and Sentinel-2 `tile_id`.
