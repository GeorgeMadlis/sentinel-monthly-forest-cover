# Monthly road-like NDVI investigation — scientific protocol

## Frozen upstream references

- Forest Cover Lab: `c322e89fb96def2434c62776ac595f6cd995ef92`; candidate graph revision `f70789df04b79ca8ec65e0094c571e0b3f6844afa2b88af2f8c9bcf1776a20f7`.
- Sentinel implementation: `2f512fec185d1290ab5203c8892231f2d5c219be`.
- AOI: `configs/aoi.example.geojson`; `example_aoi`, WGS84 rectangle 24.4–24.9 E, 58.2–58.6 N.
- Historical review to **read, not overwrite**: `reviews/20261006T174722Z-sentinel-road-investigation` containing `rois.geojson`, controls, `report.md`, `index.html`, `findings.json` and conflicting orthophoto metadata.

## Testable competing propositions

**H1**: Both road-like alignments existed before June 2025; NDVI anomaly arises on surrounding vegetation or mixed road/vegetation edges.
**H2**: Roads existed but roadside clearance, widening, resurfacing or soil/moisture conditions changed in the interval.
**H3**: Part of a newly constructed connecting road/rail/forestry track is present.
**H4**: Single-scene selection, sample count, phenology, reflectance calibration, scene registration or SCL handling creates spurious linear signals.
**H5**: A genuine forest disturbance occurs in contiguous non-road forest, which must be separately tested using a forest baseline rather than inferred from NDVI alone.

## Measurement definition

The default primary pair is *full calendar June* in 2025 and 2026 using half-open UTC windows `[2025-06-01,2025-07-01)` and `[2026-06-01,2026-07-01)`. The use of June is a provisional default motivated by archived June acquisition dates, not an assertion that the user's intended month is necessarily June. Preserve July and August same-month comparisons as preregistered sensitivity analyses. Never replace June with a June–August scene ranking without re-labeling the quantity.

For each valid S2 L2A acquisition compute NDVI = (NIR - Red)/(NIR + Red) using band calibration and quality mask. Aggregate **NDVI per observation, then take a pixelwise arithmetic mean** for each year-month; also compare the per-pixel median as a robust sensitivity; record per-pixel counts, valid timestamps, masks, pixel grid and calibration. Exclude pixels with fewer than three valid acquisitions in either month in the main experiment (sensitivity minimum 2 or 5). Do not transform missing evidence to zero.

Record `delta_abs=NDVI_2026_month-NDVI_2025_month`. For an interpretable relative metric use `delta_rel=delta_abs/max(abs(NDVI_2025_month),0.1)` only where `NDVI_2025_month >= 0.2`, because division near zero and NDVI sign changes can amplify small values. Treat this as a declared operational diagnostic, not the only scientifically valid normalization; alternative denominator sensitivity must be recorded. Pixels outside its domain are undefined for relative interpretation, not unchanged.

Maintain a common 20 m EPSG:6933 analysis grid to match archived analysis and test 10 m native optical grid separately. Check independent georegistration at multiple stable features and verify cloud/shadow/SCL handling and any radiometric offset override. Quantify absolute vs relative anomalies, road-core vs verge vs 20/40/80m bands, controls, forest vs agriculture vs other classes, and optical-only vs paired SAR. Use an explicit forest mask version and forest definition for any reported *forest loss*; without one report all-land-cover signal only. Area measurements are equal-area hectares, and any change in validity denominator must be explicit. No threshold yields ground truth without external validation.

Optical/SAR comparisons must identify actual acquisition periods and SAR orbits. Spatial overlap of two sensors is correlated evidence, not independently established cause. Historical orthophotos must distinguish source flight date from 2025 mosaic year and from WMS retrieval date. The October 6 review's metadata contradiction is a mandatory blocking/uncertainty item until resolved.

## Acceptance evidence

Each ROI gets a time-aligned visual stack, anomaly maps, per-year histogram & valid-pixel counts, multi-method sensitivity, road/rail identification matrix, source lineage, uncertainty and a falsifiable conclusion class: `supported`, `contradicted`, `indeterminate`, `not_tested`. Preserve negative findings and alternative explanations. A statement about *new road construction* needs independently dated evidence about physical alignment, not only an NDVI decrease.

## Existing reusable skills

`sentinel-monthly-forest-cover/.codex/skills/inspect-sentinel-change`, `research-sentinel-change`, `corroborate-sentinel-change`, `report-sentinel-change`. Select and record actually loaded files. Port the same written task contracts explicitly to Claude Code and general chat; do not claim that Codex skills auto-load elsewhere.
