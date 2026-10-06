# Input/provider contract

Scientific IDs are `DS-0002` (Sentinel-2), `DS-0003` (Sentinel-1), and the explicitly
supplied baseline forest dataset (for example `DS-0001`). GEE collection identifiers in
historical runs remain evidence, not required production asset sources. The user selects
and records current collection/edition; the pipeline does not infer yearly updates.

## Local inventory

```json
{"items": [{"id": "scene-id", "datetime": "2026-06-05T10:00:00Z",
  "geometry": {"type": "Polygon", "coordinates": [[[24,58],[25,58],[25,59],[24,59],[24,58]]]},
  "properties": {}, "assets": {"red": {"href": "red.tif", "band": 1,
  "scale": 0.0001, "offset": 0}, "nir": {"href": "nir.tif", "scale": 0.0001}}}]}
```

Paths resolve relative to the inventory. IDs must be unique. Item footprints are
EPSG:4326. Assets must be georeferenced; nodata must be encoded in the raster. Observation
timestamps may be date-only (UTC) or ISO timestamps. Optical bands use physical surface
reflectance after scale/offset; index calculations occur **before** temporal compositing.
Required names: `red`, `nir`, plus `swir1` for NDMI and `swir2` for NBR.

Pixel quality must be declared as `scl` with a mapped `scl` asset and explicit accepted
classes, or documented `pre-masked` calibrated assets. Pre-masked data must already
exclude clouds, shadows and sensor-invalid pixels; this declaration is not independent
verification. Cloud fraction is not inferred from valid coverage (which also includes
other missingness). Empty periods produce all-nodata composites and zero observation
counts, never fake clear pixels. Minimum observations and tile validity are configurable.

## STAC

Providers declare `type: stac`, `endpoint`, `collection`, `asset_map` and optional equality
`filters`. Asset maps convert collection-specific keys to the names above or `VV`, `VH`.
PySTAC-Client performs spatial/time queries with pagination; the exclusive end date is
also enforced locally. Collection metadata/checksums/ETags in item assets are retained.
STAC `raster:bands` scale/offset is respected, with explicit asset calibration taking
precedence. For STAC assets lacking calibration metadata, declare provider
`asset_calibration: {red: {scale: 0.0001, offset: 0}, nir: {scale: 0.0001, offset: 0}}`
using the reviewed collection edition; do not assume that these example values fit
every Sentinel processing baseline. Authenticated/signed URLs require catalogue-ready URLs or an external adapter;
no account-specific signing is implemented. ETags/checksums are not independently fetched
when absent. Local files are SHA-256 fingerprinted. Do not commit live observation lists.

## SAR assumptions

Required preprocessing metadata: `orbit_direction`, `relative_orbit`, `instrument_mode`,
`terrain_flattening`, `speckle_treatment`. Every selected item must match
`sat:orbit_state`, `sat:relative_orbit`, `sar:instrument_mode` and contain both
`sar:polarizations` VV/VH. Filtering may select a compatible geometry; missing/mixed
metadata fails. Multiple tracks require separate runs, not silent mixing.

Units are explicitly `db` or positive `linear` power (converted to dB **before** mean/median).
Features are VV, VH and `VV_MINUS_VH_DB = VV_dB − VH_dB`, the log representation of the
linear power ratio. Changes always use current minus reference. Per-feature drop
thresholds are required. Terrain flattening, incidence-angle correction and speckle
filtering are not implemented; upstream processing must be reviewed. CRS, resolution,
nodata, resampling and aggregation appear in run evidence.

## Forest gating

Accept an approved external baseline with dataset ID, version, reference year/date,
threshold, `transformation: threshold-gte`, optional band and local path. Source hashes
are recorded. For a binary mask threshold is usually 1. For Hansen-derived intact
forest, supply a previously transformed baseline accounting for loss through the chosen
reference year; the pipeline does not invent that transformation from vegetation indices.
Forest definition remains external and is not a legal classification inferred from NDVI.
