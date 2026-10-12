"""Load the raw per-location CSVs into DuckDB as source tables.

For each location in the regions CSV, reads `data/raw/<location>.csv` and
(re)creates `locations.<location>` in the DuckDB database, with `scene_id`
renamed to `<location>_scene_id`. The CSVs are only
read, never written. Run this before `dbt build`; the database file is
gitignored, so a fresh clone rebuilds it from the committed CSVs.

Usage:
    python scripts/load_raw.py
    python scripts/load_raw.py --db eurosat.duckdb --raw data/raw --regions seeds/regions.csv
"""

import argparse
import csv
from pathlib import Path

import duckdb

SCHEMA = "locations"

# Explicit types so DuckDB doesn't guess: processing_version stays a string
# ("05.10", not 5.1) and statistics is stored as JSON for staging to unpack.
COLUMN_TYPES = {
    "scene_id": "varchar",
    "tile_id": "varchar",
    "platform": "varchar",
    "acquired_at": "timestamptz",
    "published_at": "timestamptz",
    "updated_at": "timestamptz",
    "processing_version": "varchar",
    "cloud_cover": "double",
    "statistics": "json",
}


def read_locations(regions_path):
    with open(regions_path, newline="") as f:
        return sorted(row["location"].strip() for row in csv.DictReader(f) if row["location"].strip())


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--db", default="eurosat.duckdb", help="DuckDB database file")
    parser.add_argument("--raw", default="data/raw", help="folder holding <location>.csv files")
    parser.add_argument("--regions", default="seeds/regions.csv", help="CSV with a location column")
    args = parser.parse_args()

    locations = read_locations(args.regions)
    if not locations:
        raise SystemExit(f"No locations found in {args.regions}")

    columns = ", ".join(f"'{name}': '{type_}'" for name, type_ in COLUMN_TYPES.items())
    con = duckdb.connect(args.db)
    con.execute(f"create schema if not exists {SCHEMA}")

    for location in locations:
        path = Path(args.raw) / f"{location}.csv"
        table = f"{SCHEMA}.{location}"
        if not path.exists():
            raise SystemExit(f"Missing {path}")
        con.execute(
            f"""
            create or replace table {table} as
            select * rename (scene_id as {location}_scene_id)
            from read_csv(?, header = true, columns = {{{columns}}})
            """,
            [str(path)],
        )
        count = con.execute(f"select count(*) from {table}").fetchone()[0]
        print(f"Loaded {count} rows into {table}")

    con.close()


if __name__ == "__main__":
    main()
