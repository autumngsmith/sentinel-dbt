This project uses the **catalog of Sentinel-2 satellite photos**: a list describing each photo, not the photos themselves.

## The basics
- **Sentinel-2** is a set of European Space Agency (ESA) satellites that photograph all of Earth's land every few days. 
- **Scene:** one photo of one area at one moment. This is the main thing being counted.
- **Tile:** Earth is divided into a fixed grid of squares about 110 km across, each with a code like `30TVK`. Every scene belongs to one tile. A "region" in this project is a tile that has been selected and given a name.
- **Two processing levels:**
  - **Level-1C (L1C):** the raw photo as captured.
  - **Level-2A (L2A):** the same photo after ESA corrects it for the atmosphere and runs its analysis on it (cloud detection and so on). Some raw scenes never get an L2A version, which is why "processed" is its own funnel stage.
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

That scene is a good example of one that drops out of the funnel at the first quality check: it was captured and processed, but it's not clear and not full coverage.

## How it turns into a funnel
For each region and month, scenes are counted at each stage:

**captured** (L1C exists) → **processed** (L2A exists) → **mostly clear** (<50% cloud) → **clear** (<10% cloud) → **full coverage** (<5% nodata) → **usable** (clear and full coverage)

Each of those stages is one row in `funnel_metrics.csv`, which drives the monster model.

## Scale
12 tiles over roughly 5 years, at a few scenes per tile per week, in two collections: around **10,000 rows** in total.
