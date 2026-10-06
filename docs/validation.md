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

Remaining limits: no live satellite-catalogue or country-scale performance benchmark;
no implemented terrain flattening, speckle treatment, incidence correction, temporal
persistence or independent national validation; no authenticated URL signing; no RGB
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
