# Local optical/radar comparison

Run without Google Earth Engine:

```sh
.venv/bin/python -m forest_change.sigma_sar_map
```

The default input is `runs/aoi-s2-jja-2025-2026-calibrated`. The separate output is
`runs/aoi-s2-s1-jja-2025-2026-sigma`. Original artifacts are preserved. Open
`comparison.html` to compare the original fixed optical test, fixed optical test
with radar confirmation, optical-only sigma test, and sigma test with radar.
All maps work offline using the original vendored Leaflet runtime.
The original map is copied into `maps_original`, so the comparison folder can be
moved or downloaded independently. `leaflet-comparison.zip` includes all four
maps, the comparison page and metrics, without the large satellite source rasters.
Extract the ZIP and open `comparison.html` inside the extracted folder.

## Decision

For each pixel, NDVI target minus reference mean must be strictly less than
`-k * reference population standard deviation`. Default k is 2. The target is
exactly the original selected 20 June 2026 scene. Reference variability uses a
bounded sample of up to eight unique 2025 summer dates from the original archived
scene ranking. Selected scenes must have at least 50% clear AOI coverage and the
already-applied BOA-offset flag. Each pixel is SCL-masked separately. The highest
ranked eight dates are used, not all observations or an average of annual seasons.
At least two valid samples and positive standard deviation are required per pixel.
Otherwise the sigma decision is unavailable. NDVI is calculated before aggregation.

Radar uses Planetary Computer's radiometrically terrain-corrected Sentinel-1
collection, not uncalibrated GRD DN. Source linear intensity is converted to dB
using `10 * log10(value)` before temporal median compositing. Nonpositive intensity
is unavailable. Reference and target are the same June–August 2025/2026 periods
as the optical test. Both periods use one common IW VV/VH relative orbit and orbit
direction. Only scene footprints covering the entire AOI are admitted. Duplicate
acquisition dates are removed. If a period exceeds twelve scenes, twelve evenly
spaced dates are selected. The selected track and exact items/dates are archived.
There is no spatial speckle filter; temporal median is the declared treatment.

A combined candidate requires all three tests:

```
NDVI_target - mean(NDVI_reference) < -2 * std(NDVI_reference)
VV_target_median_db - VV_reference_median_db < -1.5 dB
VH_target_median_db - VH_reference_median_db < -1.0 dB
```

The existing tiled local Workflow calculates features, statistics, radar changes,
AND fusion and diagnostics on the original 20 m EPSG:6933 grid. Paired missing
sensor evidence remains nodata. No forest baseline is applied, matching the
original comparison run. Areas represent all-land-cover candidates.
The comparison runner explicitly calculates median reference radar rasters before
the change stage. The generic pooled-reference workflow otherwise uses a mean;
this override is recorded in composite metadata and the comparison manifest.

## Comparability and evidence

The display uses the exact original reference/target RGB sources, fixed
reflectance stretch, gamma, Web Mercator bounds, red overlay and yellow AOI.
The runner verifies original source checksums and byte-identical generated RGB PNGs.
The sigma test necessarily changes the optical reference from a single scene to
multiple observations. Use `maps_fixed_sar` versus the original map to isolate
radar's effect; use `maps` versus `maps_ndvi_sigma` to isolate radar under sigma.
Different valid-pixel coverage is recorded in `comparison_metrics.json`.
Radar summarizes the whole summer while target NDVI is a single June observation;
their evidence windows overlap but do not establish the same disturbance date.

`maps/anomaly_leaflet.html` is the combined sigma result.
`maps_ndvi_sigma/anomaly_leaflet.html` is its optical-only control.
`maps_fixed_sar/anomaly_leaflet.html` adds the same radar confirmation to the
original fixed NDVI decision. Each map's metadata documents its actual method.

AOI source windows are cached with grid, item, URL, calibration and SHA-256.
Reruns verify those records. Expiring Planetary Computer SAS credentials are not
stored. Frozen catalogue queries, selections, workflow config, per-band rasters,
per-pixel counts, reference standard deviation and changes remain in the run.
`execution_status.json` records success or failure. Candidate change is not
confirmed forest loss or proof of a cause. Thresholds are experimental parameters.

Override defaults with `--k`, `--reference-scenes`, `--radar-scenes`, `--vv-drop`,
`--vh-drop`, `--optical-run`, `--aoi`, and `--output`. Use a new output directory
when changing the workflow configuration or area.
