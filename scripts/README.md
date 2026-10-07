# Production scripts

The six stage/report commands use `--manifest`, `--forest-def`, `--aoi-geojson`, and
optional `--output-prefix`. Use the root README demo to create local synthetic inputs.

| Script | Work |
|---|---|
| run_pipeline.py | All stages |
| build_monthly_composites.py | Live discovery, config snapshot, per-feature composites/counts |
| compute_ndvi_anomaly.py | Change rasters for all configured optical/SAR features |
| estimate_loss_area.py | Forest gating, sensor candidates, fusion/disagreement, MMU, area |
| export_reporting_artifacts.py | CSV, GeoJSON, QA PNG, HTML evidence viewer, manifest/report |
| render_final_map.py | Refresh reporting after area stage |
| create_synthetic_fixture.py | Tiny deterministic raster/inventory inputs |
| explain_semantic_path.py | Resolve a config against the pinned Lab graph (no data access) |
| run_annual_2024_assessment.py | Migration message for preserved optional GEE example |

Run stages in table order. They use `forest_change/`; production imports do not require EE.
`common.py` retains only basic IO helpers. GEE credentials are accepted as deprecated
flags solely to give a clear migration error, not for local execution.

`run_anomaly_map_test.py --aoi configs/aoi.example.geojson` uses the existing
STAC/provider/raster/workflow boundaries to select two real observations and build
an offline Leaflet RGB/anomaly map. See [configuration and access rules](../docs/anomaly_map_test.md).

`build_review_site.py REVIEW [--strict] [--zip]` makes an investigation folder under
`reviews/` browsable offline: `index.html`, per-folder listings and Markdown/JSON/CSV
viewers under `_html/`, a SHA-256 inventory and a relative-link check. The
`.codex/skills/*-sentinel-change` skills run it at the end of every stage.
