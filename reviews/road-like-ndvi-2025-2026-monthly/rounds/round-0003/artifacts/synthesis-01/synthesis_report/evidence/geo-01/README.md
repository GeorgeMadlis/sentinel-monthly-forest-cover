# geo-01 — national geospatial evidence (round-0002, retask 0001)

Role: `national-geospatial-evidence`. Host: Claude Code subagent spawned by synthesis-01.
Executed 2026-10-24 between 16:37 and about 16:55 UTC. I worked independently: I read no Sentinel/EO
conclusions or audit-01 reports. Every source is from Maa- ja Ruumiamet (MaRu), retrieved
2026-10-24 and used under its open-data licence. Attribution: "Maa- ja Ruumiamet".

## Key findings

**G3: flight dates resolved.** The WMS `metainfo` value `LENNUAEG 09.06.2023` is stale. The
official per-sheet download listings (geoportaal page 610) name the files by flight date:

| Sheets | RGB flights (newest first) | NGR |
|---|---|---|
| 53733, 53734, 53832, 53841, 53843, 53844 (ROI-01); 53922, 53931, 53833 (ROI-02); 53932 (CONTROL-01) | **2025-04-03**, 2023-06-09, 2021-04-19, 2019-06 … | 2023-06-09 |
| 53642 (CONTROL-02) | 2025-04-27, 2023-06-09 | 2023-06-09 |
| 1:2000 low-altitude sheets 476534/478535 (ROI-01 SW end) | 2024-05-03, 2022-04-20 | – |
| 494529 (ROI-02 N end) | 2024-05-04 | – |

- The `of2025aero` pixels are from the 2025-04-03 flight. That date is **before July 2025**, and the images are leaf-off.
- The June 2023 flight is served as WMS layer `of2023mets`. `of2023aero` has no pixels here.
- The current `EESTIFOTO` is the same 2025-04-03 imagery.
- **No orthophoto taken after 2025-04-03 exists** for any ROI sheet. There is no 2026 file and no `of2026*` layer.

**G1: presence of a feature along the ROI axis**

| ROI | 2023-06-09 | 2024 | 2025-04-03 (pre-July) | Post-July 2025 / 2026 imagery | Maps: 2024 / 2026 editions, ETAK 2026-10-24 |
|---|---|---|---|---|---|
| ROI-01 | absent (S0–S3) | absent at S0 (2024-05-03); unavailable elsewhere | absent (S0–S3 and 10 m overview) | **unavailable** | no aligned feature |
| ROI-02 | absent (S1, S2) | unavailable | absent (S1, S2 and overview) | **unavailable** | no aligned feature |
| Controls | not inspected | – | not inspected | unavailable | no 2025–26 edits |

- **ROI-01:** only older features cross the buffer: gravel roads, forest tracks, ditches and sihts. Between 2023-06 and 2025-04, new clear-fell blocks appeared inside or next to the buffer at S0, S1 and S2. These are block-shaped and run obliquely to the axis, so they do not form a linear corridor.
- **ROI-02:** an existing paved two-lane road runs just east of and parallel to the buffer. It appears in both years.
- **ETAK:**
  - The longest single feature inside either buffer is 255 m (ROI-01) or 85 m (ROI-02). All of these are crossings.
  - Edits dated 2025–2026 touch only crossing features: power lines re-edited in 2026-01 to 2026-03, a broad-gauge rail geometry change on 2026-08-10 and some short road pieces.

**G2: width.** Beside ROI-02-S1, the bright paved surface of the existing road measures about
10.6 m (2023) and about 10.0 m (2025), ±1.5 m. That is no detectable widening before July 2025.
Change across July 2025 cannot be tested because no post-July imagery exists. ROI-01 has no
carriageway along its axis to measure.

## Images (`images/`; each tile is 600 × 600 m at 0.6 m/px, magenta = ROI 40 m buffer outline)
- `<SITE>_composite_2023-2025-maps.png` is a 2×2 grid:
  - top: the 2023-06-09 and 2025-04-03 orthophotos
  - bottom: the 2024 and 2026 basic-map editions
- Sites: ROI-01-S1 (536303, 6478722), ROI-01-S2 (540513, 6483500), ROI-01-S3 (545475, 6487533), ROI-02-S1 (529798, 6491903), ROI-02-S2 (531476, 6488012). Coordinates are EPSG:3301.
- `ROI-01-S0_composite_2023-2024-2025.png` shows the SW end (535000, 6476700) for 2023-06-09, 2024-05-03 and 2025-04-03.
- Individual tiles are named `<SITE>_<layer>_flight-YYYY-MM-DD.png` or `_map-edition-YYYY.png`.
- The overviews are in `raw/wms/ROI-0?_overview_of2025aero.jpg` and have no overlay.

## Negative results and limitations
- I inspected about 2.4 km of ROI-01 (about 22.5 km) and about 1.2 km of ROI-02 (about 6.4 km) at feature scale. The rest was seen only in a ~10 m/px overview, which cannot resolve features narrower than about 10–20 m.
- Flight dates come from official file names. I did not download the GeoTIFFs and did not read their embedded metadata.
- The match between WMS layer and flight is inferred from three things: the listings, leaf-on versus leaf-off appearance, and the pixel equality of EESTIFOTO and of2025aero.
- I did not retrieve a positional-accuracy statement. Features line up between years to within a few metres (visual check).
- Map absence is weak evidence for a recent change:
  - Basic-map sheets were field-mapped in 2007, 2008 and 2022 (`PK_AASTA`).
  - The ETAK update lag is unknown.
  - ETAK is partly derived from the same orthophotos, so maps and images share lineage and are not independent confirmation.
- A mapped road can predate any construction project, and a current map does not date a change.
- The control sites were checked with ETAK only.
- A first low-altitude listing request without a User-Agent returned empty responses. I discarded those and repeated the requests.
- None of this establishes legal deforestation, the cause of any change, or confirmed forest state.

## Files
- `geo_sources.csv` is the source inventory.
- `geo_claims.csv` contains the claims.
- `geo_primary_evidence.json` lists every artifact with its SHA-256, URL, retrieval time, acquisition date, lineage and any missing inputs.
- `raw/` holds the downloads. `raw/fetch_log.jsonl` has the exact URL of every GetMap request.
- `scripts/` holds the helper scripts.
- `execution.json` is the execution record.
