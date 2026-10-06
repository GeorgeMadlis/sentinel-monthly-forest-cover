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
| run_annual_2024_assessment.py | Migration message for preserved optional GEE example |

Run stages in table order. They use `forest_change/`; production imports do not require EE.
`common.py` retains only basic IO helpers. GEE credentials are accepted as deprecated
flags solely to give a clear migration error, not for local execution.
