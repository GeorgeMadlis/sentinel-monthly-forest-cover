# Real Sentinel-2 anomaly map test

```sh
.venv/bin/python scripts/run_anomaly_map_test.py \
  --manifest configs/anomaly-map.example.yaml \
  --aoi configs/aoi.example.geojson
```

The test configuration adapts the existing seasonal example to **two** periods:
2025-06-01 through 2025-08-31 (reference), and 2026-06-01 through 2026-08-31
(target), inclusive. Catalogue queries end exclusively on September 1. It chooses
one best usable L2A observation per period; it does not claim that one scene is a
seasonal composite. Actual acquisition dates can differ within these periods.
This is an execution/QA experiment, not a scientifically validated forest-loss study.

`forest_change/selection.py` assesses every discovered scene's SCL on a 200 m
EPSG:6933 grid. Ranking is lexicographic: descending fraction of non-nodata,
nondefective AOI pixels; ascending fraction of cloud/shadow among those pixels
(SCL 3/8/9/10); ascending scene cloud percentage; distance to period midpoint;
item ID. At least one clear AOI pixel is required. SCL 4/5/6/7 is accepted for
analysis. Coarse ranking can miss small clouds; source reflectance validity is
checked during feature calculation. Ranking is bounded to eight concurrent reads.
All candidate metrics and mapped source assets are archived, including rejected
candidates. No scene records enter the Lab graph.

`forest_change/asset_access.py` verifies byte-range responses before remote COG
use. Exact cached sources require matching item/asset/URL/acquisition provenance,
SHA-256 and a readable georeferenced raster. Failed range/window access or an
explicit `--asset-access cache` request materializes a complete source under the
run's `cache/`, with size, checksum and download time. `--asset-access remote`
forbids fallback. Existing local rasters are validated. The default is `auto`.
Remote source windows are materialized as **derived AOI rasters**, calibrated once,
under `source_windows/<role>/`; these are not downloaded complete Sentinel tiles.
Their source URLs, source calibration and hashes remain in evidence.

The production `Workflow` calculates NDVI before compositing. Each period has
one selected scene; therefore its median equals that observation, and the
reference mean equals its sole period composite. Change is target minus
reference; strict change < -0.2 is flagged. Both NDVI values must be finite.
The existing optical-only fusion and component filter are used (minimum one
pixel, no smoothing or persistence). The analysis grid is 20 m EPSG:6933.
No approved external forest baseline is present for this AOI. Explicit
`forest_mask: null` requests ungated screening and records no baseline dataset
in semantic provenance. Candidate hectares include all land covers and must not
be interpreted as forest-loss area. Existing forest-gated workflows retain their
configured masks. Cloud-edge bilinear mixing, phenology, agriculture, moisture,
SCL errors and calibration remain QA limitations. The selected Earth Search COGs declare `earthsearch:boa_offset_applied: true`
but retain an asset offset of -0.1. Applying that offset twice produced mostly
negative RGB reflectance and invalid-looking imagery. The explicit provider
`asset_calibration` override uses gain 0.0001 and offset 0; selected items must
satisfy `calibration_requirements` before use. Original metadata remains archived.
This interpretation is supported by the provider's statement that some COGs
are offset-corrected, its [known metadata issue](https://github.com/Element84/earth-search/issues/66),
and the observed pixel distributions. It is a documented radiometric inference,
not independent surface-reflectance validation. The initial metadata-only result
is retained separately as rejected QA evidence and is superseded by the calibrated run.


`forest_change/leaflet.py` reprojects all visualization layers onto the same
Web Mercator grid. RGB uses B04/B03/B02, a fixed reflectance range 0–0.3 and
gamma 2.2 for both dates. SCL/nodata areas are transparent. Anomalies use nearest
neighbour and red RGBA; non-anomalies/nodata are transparent. Analytical layer
control contains exactly reference, target and detected anomalies. Target and
anomalies are initially visible; AOI is always outlined. The information panel
records method, threshold, periods, acquisitions, item IDs and provider.

The map embeds PNGs and uses vendored Leaflet 1.9.4 JS/CSS/icons. Open
`runs/aoi-s2-jja-2025-2026-calibrated/maps/anomaly_leaflet.html` directly with no server or
internet required. PNGs remain separately available for inspection. Complete
source URLs and per-band access decisions are in `selected_observations.json`;
queries in `catalogue_queries.json`; outputs and semantic evidence in
`run_manifest.json`; numerical counts/area in `anomaly_metrics.json`.
`execution_status.json` records failures honestly. Live scene lists and raster
outputs stay local rather than entering version control.

Unit tests use tiny synthetic data only. Run `.venv/bin/python -m unittest discover -v`.

To replay a prior run after a documented linear calibration review, preserving
its original discovery/selection and avoiding repeated remote reads:

```sh
.venv/bin/python scripts/run_anomaly_map_test.py \
  --replay-from runs/aoi-s2-jja-2025-2026
```

Replay requires a new output directory, identical AOI/grid/periods and verified
SHA-256 of every source window. It inverts the previously recorded linear
calibration and applies the configured one, preserving nodata. Each derived
source records its prior path/hash, old/new calibration and processing access
mode. Original acquisition used remote COG; replay processes existing derived
AOI rasters. This is not a complete-tile source cache. Archived query timestamps
are retained and the inventory identifies a selected view of archived queries.
