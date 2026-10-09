"""Fetch Sentinel-2 scene metadata from the Copernicus Data Space STAC catalog.

Reads the locations to fetch from a regions CSV (`location` and `tile_id`
columns), searches the processed (L2A) collection for each location's tile over
a date range, and writes one CSV per location with one row per scene. Each
location's file stands in for a separately ingested source table.

Usage:
    python scripts/fetch_scenes.py
    python scripts/fetch_scenes.py --start 2025-01-01 --end 2025-12-31 \
        --regions seeds/regions.csv --out data/raw
"""

import argparse
import csv
import json
import time
from pathlib import Path

from pystac_client import Client
from pystac_client.exceptions import APIError

STAC_URL = "https://stac.dataspace.copernicus.eu/v1"
COLLECTION = "sentinel-2-l2a"

# The catalog rate-limits bursts of requests (HTTP 429), so pause between tiles
# and back off before retrying a tile that gets limited.
PAUSE_SECONDS = 3
MAX_ATTEMPTS = 5

COLUMNS = [
    "scene_id",
    "tile_id",
    "platform",
    "acquired_at",
    "published_at",
    "updated_at",
    "processing_version",
    "cloud_cover",
    "statistics",
]


def read_locations(regions_path):
    with open(regions_path, newline="") as f:
        rows = list(csv.DictReader(f))
    return sorted((row["location"].strip(), row["tile_id"].strip()) for row in rows if row["location"].strip())


def scene_row(item, tile_id):
    props = item.properties
    return {
        "scene_id": item.id,
        "tile_id": tile_id,
        "platform": props.get("platform"),
        "acquired_at": props.get("datetime"),
        "published_at": props.get("published"),
        "updated_at": props.get("updated"),
        "processing_version": props.get("processing:version"),
        "cloud_cover": props.get("eo:cloud_cover"),
        # Kept as raw JSON; unpacked into columns in the staging model.
        "statistics": json.dumps(props.get("statistics"), sort_keys=True),
    }


def fetch_tile(client, tile_id, start, end):
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            search = client.search(
                collections=[COLLECTION],
                datetime=f"{start}/{end}",
                filter={"op": "=", "args": [{"property": "grid:code"}, f"MGRS-{tile_id}"]},
                filter_lang="cql2-json",
                limit=100,
            )
            rows = [scene_row(item, tile_id) for item in search.items()]
            # Sorted so re-running the fetch gives a clean git diff.
            return sorted(rows, key=lambda r: (r["acquired_at"], r["scene_id"]))
        except APIError as error:
            if attempt == MAX_ATTEMPTS:
                raise
            wait = 15 * attempt
            print(f"  {tile_id}: {error}; retrying in {wait}s", flush=True)
            time.sleep(wait)


def write_csv(rows, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--regions", default="seeds/regions.csv", help="CSV with location and tile_id columns")
    parser.add_argument("--start", default="2022-01-01", help="first acquisition date (inclusive)")
    parser.add_argument("--end", default="2026-09-30", help="last acquisition date (inclusive)")
    parser.add_argument("--out", default="data/raw", help="output directory")
    args = parser.parse_args()

    locations = read_locations(args.regions)
    if not locations:
        raise SystemExit(f"No locations found in {args.regions}")

    client = Client.open(STAC_URL)
    end = f"{args.end}T23:59:59Z"
    out_dir = Path(args.out)

    for location, tile_id in locations:
        rows = fetch_tile(client, tile_id, args.start, end)
        path = out_dir / f"{location}.csv"
        write_csv(rows, path)
        print(f"Wrote {len(rows)} rows to {path}", flush=True)
        time.sleep(PAUSE_SECONDS)


if __name__ == "__main__":
    main()
