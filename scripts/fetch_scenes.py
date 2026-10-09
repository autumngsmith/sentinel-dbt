"""Fetch Sentinel-2 scene metadata from the Copernicus Data Space STAC catalog.

Reads the tiles to fetch from a regions CSV (a `tile_id` column, e.g. 30TVK),
searches the raw (L1C) and processed (L2A) collections for each tile over a
date range, and writes one CSV per collection with one row per scene.

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

# The catalog rate-limits bursts of requests (HTTP 429), so pause between tiles
# and back off before retrying a tile that gets limited.
PAUSE_SECONDS = 3
MAX_ATTEMPTS = 5

COLLECTIONS = {
    "l1c": "sentinel-2-l1c",
    "l2a": "sentinel-2-l2a",
}

BASE_COLUMNS = [
    "scene_id",
    "tile_id",
    "platform",
    "acquired_at",
    "published_at",
    "updated_at",
    "processing_version",
    "cloud_cover",
]


def read_tiles(regions_path):
    with open(regions_path, newline="") as f:
        tiles = [row["tile_id"].strip() for row in csv.DictReader(f)]
    return sorted({t for t in tiles if t})


def scene_row(item, tile_id, include_statistics):
    props = item.properties
    row = {
        "scene_id": item.id,
        "tile_id": tile_id,
        "platform": props.get("platform"),
        "acquired_at": props.get("datetime"),
        "published_at": props.get("published"),
        "updated_at": props.get("updated"),
        "processing_version": props.get("processing:version"),
        "cloud_cover": props.get("eo:cloud_cover"),
    }
    if include_statistics:
        # Kept as raw JSON; unpacked into columns in the staging model.
        row["statistics"] = json.dumps(props.get("statistics"), sort_keys=True)
    return row


def fetch_tile(client, collection, tile_id, start, end, include_statistics):
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            search = client.search(
                collections=[collection],
                datetime=f"{start}/{end}",
                filter={"op": "=", "args": [{"property": "grid:code"}, f"MGRS-{tile_id}"]},
                filter_lang="cql2-json",
                limit=100,
            )
            return [scene_row(item, tile_id, include_statistics) for item in search.items()]
        except APIError as error:
            if attempt == MAX_ATTEMPTS:
                raise
            wait = 15 * attempt
            print(f"  {collection} {tile_id}: {error}; retrying in {wait}s", flush=True)
            time.sleep(wait)


def fetch_collection(client, collection, tiles, start, end, include_statistics):
    rows = []
    for tile_id in tiles:
        tile_rows = fetch_tile(client, collection, tile_id, start, end, include_statistics)
        print(f"  {collection} {tile_id}: {len(tile_rows)} scenes", flush=True)
        rows.extend(tile_rows)
        time.sleep(PAUSE_SECONDS)
    # Sorted so re-running the fetch gives a clean git diff.
    return sorted(rows, key=lambda r: (r["tile_id"], r["acquired_at"], r["scene_id"]))


def write_csv(rows, columns, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--regions", default="seeds/regions.csv", help="CSV with a tile_id column")
    parser.add_argument("--start", default="2022-01-01", help="first acquisition date (inclusive)")
    parser.add_argument("--end", default="2026-09-30", help="last acquisition date (inclusive)")
    parser.add_argument("--out", default="data/raw", help="output directory")
    args = parser.parse_args()

    tiles = read_tiles(args.regions)
    if not tiles:
        raise SystemExit(f"No tiles found in {args.regions}")

    client = Client.open(STAC_URL)
    end = f"{args.end}T23:59:59Z"
    out_dir = Path(args.out)

    for name, collection in COLLECTIONS.items():
        include_statistics = name == "l2a"
        rows = fetch_collection(client, collection, tiles, args.start, end, include_statistics)
        columns = BASE_COLUMNS + (["statistics"] if include_statistics else [])
        path = out_dir / f"scenes_{name}.csv"
        write_csv(rows, columns, path)
        print(f"Wrote {len(rows)} rows to {path}")


if __name__ == "__main__":
    main()
