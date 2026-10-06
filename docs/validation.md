# Validation record — 2026-10-06

The baseline repository had no discoverable tests (unittest discovery: zero tests).
The suite contains 24 passing tests (21 from the initial migration, 3 added by the
cross-repository audit below) covering:

- NDVI/NDMI/NBR, log SAR ratio, mean/median/population std and missingness;
- calendar months including leap dates, moving-window generation, matched seasons,
  cross-year Southern Hemisphere periods and invalid alignment parameters;
- local/STAC provider interfaces, spatial/time filtering, common-asset numerical equivalence;
- bounded raster window reads, equal-area hectares and unsuitable CRS rejection;
- forest gating, optical/SAR disagreement, missing optical evidence and explicit SAR-only use;
- component halos at tile boundaries and tile-size numerical equivalence;
- deterministic manifests on repeated reporting from the same archived inventory;
- input/config mutation rejection and successful explicit legacy monthly migration;
- production imports with EE, geemap and Google packages actively blocked;
- workflow configuration schema and the locally available Lab descriptor/provenance validators.
- Lab application-ID validation, the seasonal S1/S2 semantic example end to end, the semantic
  trace CLI, the explicit degraded SAR-only flag and no GEE packages in `requirements.txt`.

Validation command: `.venv/bin/python -m unittest discover -v`.

The standalone CLI synthetic demonstration also succeeded:

```sh
.venv/bin/python scripts/create_synthetic_fixture.py --directory /tmp/sentinel-forest-demo-validation
.venv/bin/python scripts/run_pipeline.py \
  --manifest /tmp/sentinel-forest-demo-validation/workflow.yaml \
  --forest-def /tmp/sentinel-forest-demo-validation/forest.yaml \
  --aoi-geojson /tmp/sentinel-forest-demo-validation/aoi.geojson
```

It produced 0.16 hectares of overlapping candidates, 14 optical candidate pixels,
16 SAR candidate pixels and 22 disagreement pixels. The source cloud pixel and
nonforest pixel were excluded. These are synthetic semantic checks, not satellite
accuracy results. PNG quicklook and manifest were inspected. The interactive HTML map
shows per-window tile summaries; Leaflet/basemap require internet, while QA images and
linked evidence remain local. Area summaries describe observed candidate area, not
estimated missing-pixel disturbance; check valid coverage and rejected tiles alongside area.

`pip check`, compileall and `git diff --check` pass. Production dependency closure was
inspected from installed distribution metadata: no Earth Engine, geemap or GCS
requirements are reachable. The old working environment still contains historical GEE
packages; a guarded import test demonstrates that production does not use them. A fresh
online resolver dry-run could not reach PyPI (DNS/network unavailable); installed-version
validation and dependency inspection succeeded. Tested root versions:

| Library | Version |
|---|---|
| NumPy | 2.4.4 |
| Rasterio / GDAL | 1.4.4 / recorded in each manifest |
| PyProj | 3.7.2 |
| Shapely | 2.1.2 |
| PyYAML | 6.0.3 |
| SciPy | 1.17.1 |
| Pillow | 12.2.0 |
| PySTAC-Client | 0.9.0 |
| jsonschema | 4.26.0 |

All historical Python scripts copied into `examples/gee/` match their pre-change versions
byte-for-byte, and existing `runs/` artifacts were left intact. Final diff and dependency
boundaries were inspected. The Lab pin is in `workflow.yaml`; neither Lab code nor its
canonical scientific corpus was modified.

Limits at the initial migration (live AOI test superseded below): no country-scale performance benchmark;
no implemented terrain flattening, speckle treatment, incidence correction, temporal
persistence or independent national validation; no authenticated URL signing; no seasonal RGB
composites. Thresholds remain experimental and weighted fusion is not calibrated
probability. Quality masks are applied on the target grid; bilinear interpolation can mix cloud-edge
values and requires satellite QA. Pixel-centre boundaries, resampling, provider calibration and reference
weighting can alter results; science review remains necessary. This is declared partial
method coverage, not an audited v2-compliance or production-accuracy claim.

IO design references: [Rasterio windowed IO](https://rasterio.readthedocs.io/en/stable/topics/windowed-rw.html)
and [PySTAC-Client usage](https://pystac-client.readthedocs.io/en/stable/usage.html).

## Cross-repository integration audit — 2026-10-06

Audited against Forest Cover Lab (pre-audit `c0f21c7`, post-audit `f3895e4`, graph revision
`ef90b703…`). Fixed here: descriptor tools/capabilities now match code (pyproj, shapely,
windowed IO, raster mask; NumPy aggregation recorded as a divergence instead of an
unprovided xarray capability); further partial-coverage divergences declared; `application`
must be a Lab concept ID; manifests record every Lab tool actually used and the application,
validation and non-claim concepts, with optical/SAR observation concepts limited to configured
sensors; an explicit evidence-mode/degraded SAR-only flag; BigTIFF for country-scale grids;
the legacy GEE input manifest renamed to `configs/legacy_gee_manifest.example.json`; the
forest-definition example no longer restates a canonical canopy-threshold definition.

Commands: `.venv/bin/python -m unittest discover -v` (24 OK);
`python ../forest-cover-lab/graph/build.py --check --descriptor workflow.yaml` (passes);
the README synthetic CLI demo (0.16 ha synthetic candidates, unchanged) followed by Lab
`validate_provenance` on its manifest (passes). Semantic path: `docs/semantic_example.md`.

## Real AOI anomaly map — 2026-10-06

Inspected execution commits `4df8370ccf42f127ca9c9814e40b2d81166d3932` and
`bdff928650f55dc77ba8bccc23f9a5892d753cb1` before extending their provider,
windowed raster and Workflow stages. No canonical Lab content was changed.

Executed live Earth Search `sentinel-2-l2a` discovery for
`configs/aoi.example.geojson`: 216 reference and 235 target observations. Used
2025-06-01–2025-08-31 and 2026-06-01–2026-08-31 from the existing seasonal example,
reduced to two periods and one deterministically ranked observation per period.
Selected acquisition dates were June 15, 2025 and June 20, 2026. Both had full
valid AOI coverage at the 200 m SCL assessment grid. Source bands were read using
HTTP-range COG windows; no complete source TIFFs were downloaded.

Visual QA caught conflicting provider calibration metadata: the selected COGs
mark BOA offset as already applied but retain asset offset -0.1. Metadata-only
calibration yielded mostly negative RGB reflectance. Preserved that initial run
as rejected QA evidence. The explicit gain-only override (0.0001, offset 0) is
supported by the item flag, the provider's known metadata issue and observed
pixel distributions; it remains a documented inference, not independent
radiometric validation. A guarded, checksum-verified replay into a new run
reprocessed the existing derived AOI rasters without repeating remote downloads.
Both original and corrected calibration are retained in lineage records.

Final method: NDVI target minus reference, strict < -0.2, optical-only, SCL
4/5/6/7, paired finite pixels, no forest mask, minimum component one pixel, no
persistence or smoothing, 20 m EPSG:6933. Result: 91,291 anomaly pixels,
3,651.64 hectares, 3,255,306 paired valid pixels / 3,256,200 AOI grid pixels
(99.9725%). These are ungated all-land-cover anomalies, including agriculture
and water; hectares are not forest-loss area or validated disturbance accuracy.

The portable map embeds RGB/anomaly PNGs and vendors Leaflet JS/CSS/icons.
Offline Chromium verified exactly three analytical layers, default visibility,
all toggles, image loads, AOI outline and scale bar, with zero JavaScript errors,
failed requests or external network requests. PNG screenshot inspected. An
independent recomputation from source windows matched NDVI change and the strict
threshold mask; all then-recorded output paths/checksums and Lab provenance
validated. Evidence stays local under `runs/aoi-s2-jja-2025-2026-calibrated/`.

All 32 tests pass (`.venv/bin/python -m unittest discover -v`). The suite now includes offline scene-ranking, cache reuse/fallback/provenance,
calibration guards, full runner evidence/checksums, replay/tamper detection,
transparent anomaly rendering and map bounds/layers. Production still requires
no Earth Engine dependency. Configuration/semantic trace, pinned Lab descriptor,
compileall, pip check and git diff whitespace checks pass. Coarse SCL ranking,
cloud-edge interpolation, phenology and unvalidated thresholds/calibration remain
limitations; no national-scale performance or independent accuracy claim is made.
