# Executable disturbance screening specification (2.0)

Scientific authority: pinned Forest Cover Lab contracts in `workflow.yaml`, especially
v2, ADR 0002/0003/0004/0005 and reporting/validation requirements. This document describes
implementation choices, not new canonical forest definitions or scientifically validated
thresholds. See `docs/monthly_workflow.md` and `docs/dataset_contract.md` for exact temporal
and acquisition contracts.

- NDVI = (NIR−RED)/(NIR+RED), NDMI = (NIR−SWIR1)/(NIR+SWIR1), NBR =
  (NIR−SWIR2)/(NIR+SWIR2); invalid inputs/zero denominator produce nodata.
- Features are computed per observation before mean/median compositing.
- Reference statistics use declared period-composite or pooled-observation weighting;
  standard deviation is population standard deviation (`ddof=0`).
- Change = current−reference for every feature.
- Optical candidate requires all configured optical changes < their fixed thresholds,
  or < −k×reference standard deviation. Valid baseline-mask pixels gate the result.
- SAR candidate requires all configured SAR changes < separate thresholds, in dB;
  VV_MINUS_VH_DB is a log power ratio, not raw VV/VH division of dB values.
- Fusion uses declared single-sensor, AND, OR or weighted binary-vote rules. Combined
  rules require both sensors. Agreement includes both-negative; disagreement is XOR.
- Final disturbance applies eight-connected minimum component size and rejects tiles
  below configured valid coverage. Raw sensor/fused diagnostics remain evidence.
- Area = candidate pixel count × equal-area affine determinant with metre conversions
  / 10,000 hectares. Geographic or nonequal-area grids fail before raster allocation.
- Missingness remains raster nodata (`−9999`); valid noncandidate pixels are zero.
- No unique-area sum across overlapping windows; no inference of legal deforestation,
  forest-state persistence or causality. Persistence periods >1 are unsupported and fail.

Outputs: configuration snapshot, live discovery inventory, composites/counts, reference
stats, changes, sensor/fusion/disagreement/final layers, tile/period summaries, metrics,
QA thumbnails, HTML evidence viewer, report and checksummed semantic manifest. Exported
GeoTIFFs are tiled; RGB composites and independent satellite QA are not yet implemented.
