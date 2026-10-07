# v2 Monthly Confirmation Specification

> Backend scope: GEE/EE acquisition steps below describe optional reference implementations.
> Under ADR 0005 production scientific methods must not require GEE. Equivalent open/local
> implementations must preserve all scientific rules, label semantics and non-claims.

## Goal

Produce monthly forest-related summaries using monthly Sentinel-1 SAR and Sentinel-2 optical composites, with confirmation logic to reduce false positives.

## Inputs

| Input | Format | Source |
|---|---|---|
| AOI geometry | GeoJSON or WKT in EPSG:4326 | User-supplied |
| Forest definition config | YAML | `configs/v2_defaults.yaml` (TBD) |
| v1 baseline forest mask | GeoTIFF / COG | Output of v1 run |
| Sentinel-2 L2A | EE ImageCollection | `COPERNICUS/S2_SR_HARMONIZED` |
| Sentinel-1 GRD | EE ImageCollection | `COPERNICUS/S1_GRD` |

## Outputs

| Output | Format | Path |
|---|---|---|
| Monthly S2 composite | GeoTIFF / COG per month | `outputs/<run_id>/composites/s2_<YYYY-MM>.tif` |
| Monthly S1 composite | GeoTIFF / COG per month | `outputs/<run_id>/composites/s1_<YYYY-MM>.tif` |
| Monthly forest indicator | GeoTIFF / COG per month | `outputs/<run_id>/indicators/forest_<YYYY-MM>.tif` |
| Monthly area summary | CSV | `outputs/<run_id>/monthly_area_summary.csv` |
| Run manifest | JSON | `outputs/<run_id>/run_manifest.json` |
| QA thumbnails | PNG per month | `outputs/<run_id>/qa/<YYYY-MM>.png` |

## Algorithm (high level)

1. Build monthly cloud-masked S2 composites (median; cloud probability mask).
2. Build monthly S1 SAR composites (mean VV/VH, terrain-flattened).
3. Compute monthly indicators on the v1 baseline mask only:
   - NDVI, NDMI from S2
   - VV/VH ratio from S1
4. Apply temporal persistence rule: a pixel must satisfy the forest indicator condition for **N consecutive months** (default N=2) before being labelled "confirmed forest" for the focal month.
5. Handle optical/SAR disagreement by emitting a `disagreement` flag per pixel per month.
6. Compute monthly forest area on the confirmed mask using ADR 0003 area policy.
7. Write monthly composites, indicators, and `monthly_area_summary.csv`.
8. Emit run manifest and QA thumbnails.

## Required rules

- Quality-aware compositing (cloud, shadow, sensor-quality masks)
- Temporal persistence logic must be explicit and configurable
- Optical/SAR disagreement must be flagged, not silently resolved
- Area computation per ADR 0003
- Every monthly indicator must reference the v1 baseline mask used

## Error modes

| Error mode | Mitigation |
|---|---|
| Sparse S2 coverage in cloudy months | Fall back to S1-only with explicit flag |
| AOI fully cloud-covered for a month | Emit empty composite + record gap in manifest |
| Speckle artefacts in S1 | Apply terrain flattening + Refined Lee or equivalent filter |

## Validation requirements

- Visual QA on at least 3 months per run
- Cross-check against authoritative national datasets where available
- Manifest validates against schema

## Non-claims

This v2 spec must not produce or imply:

- That annual Hansen labels are equivalent to monthly forest-state labels.
- That a single month's indicator value proves forest loss without temporal persistence.
- Disturbance attribution to a specific cause.

## References

- ADR 0001 — Default Platform (superseded by ADR 0005)
- ADR 0002 — Forest Definition
- ADR 0003 — Area Computation Policy
- ADR 0004 — Monthly Target Definition
- `specs/v1_forest_baseline.md`
