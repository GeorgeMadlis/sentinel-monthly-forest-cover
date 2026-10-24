# v1 Forest Baseline Specification

> Backend scope: GEE/EE acquisition steps below describe optional reference implementations.
> Under ADR 0005 production scientific methods must not require GEE. Equivalent open/local
> implementations must preserve all scientific rules, label semantics and non-claims.

## Goal

Produce a transparent, reproducible large-scale forest coverage baseline for a defined AOI using Hansen Global Forest Change v1.12.

## Inputs

| Input | Format | Source |
|---|---|---|
| AOI geometry | GeoJSON or WKT in EPSG:4326 | User-supplied |
| Forest definition config | YAML | `configs/v1_defaults.yaml` |
| Hansen GFC v1.12 | EE ImageCollection | `UMD/hansen/global_forest_change_2024_v1_12` |

## Outputs

| Output | Format | Path |
|---|---|---|
| Baseline forest mask | GeoTIFF / COG, `uint8`, nodata = 255 | `outputs/<run_id>/forest_mask.tif` |
| Area summary | CSV | `outputs/<run_id>/area_summary.csv` |
| Run manifest | JSON | `outputs/<run_id>/run_manifest.json` |
| HTML summary report | HTML | `outputs/<run_id>/report.html` |

## Algorithm

1. Load AOI and validate it is a single polygon or multipolygon in EPSG:4326.
2. Compute SHA-256 hash of canonical GeoJSON; record in manifest.
3. Load Hansen GFC v1.12 from Earth Engine.
4. Build forest mask:
   - `forest = (treecover2000 >= canopy_threshold_pct) AND (datamask == 1)`
5. Apply minimum mapping unit:
   - Remove connected components smaller than `min_mapping_area_ha` hectares.
6. Clip to AOI.
7. Export forest mask as COG to local disk.
8. Compute area:
   - Reproject to area CRS (default EPSG:6933) **or** use geodesic area.
   - Sum forest pixels × pixel area; convert to hectares.
9. Write `area_summary.csv` with: `aoi_id`, `forest_area_ha`, `total_aoi_area_ha`, `forest_fraction`.
10. Write `run_manifest.json` validating against `validate/run_manifest.schema.json`.
11. Render HTML report from `report/templates/v1_report.html.j2`.

## Required rules

- Exchange CRS: **EPSG:4326**
- Area CRS: **EPSG:6933** (default) or explicit geodesic method
- Area unit: **hectares**
- Threshold: declared in config (default 30 %)
- MMU: declared in config (default 0.5 ha)
- nodata: 255 in output raster
- Every run produces a valid `run_manifest.json`

## Error modes

| Error mode | Mitigation |
|---|---|
| AOI not in EPSG:4326 | Reject with clear error message |
| AOI crosses antimeridian | Split or reproject before EE query |
| EE quota exceeded | Fall back to local Hansen tile pipeline (see ADR 0001) |
| Threshold not specified | Reject; threshold must be explicit in config |
| Output area unit not hectares | Reject; unit must be hectares |

## Validation requirements

- Pass all unit tests in `tests/test_v1_*.py` before any baseline run is reported.
- Pass small-AOI integration test (≤ 10 000 ha, < 10 min runtime).
- Run manifest must validate against schema.

## Non-claims

This v1 spec must not produce or imply:

- monthly forest cover estimates
- disturbance timing claims at sub-annual resolution
- forest-loss attribution beyond the year-2000 baseline mask

## References

- ADR 0001 — Default Platform (superseded by ADR 0005)
- ADR 0002 — Forest Definition
- ADR 0003 — Area Computation Policy
- `configs/v1_defaults.yaml`
- `validate/run_manifest.schema.json`
