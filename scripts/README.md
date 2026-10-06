# Scripts Plan

This folder is for runnable pipeline scripts.

## Planned Scripts

1. build_monthly_composites.py
- Build reference and current month composites.

2. compute_ndvi_anomaly.py
- Compute NDVI and anomaly rasters.

3. estimate_loss_area.py
- Build disturbance mask and area summaries.

4. export_reporting_artifacts.py
- Export tables, GeoJSON, and quicklook images.

5. run_pipeline.py
- Orchestrates all four stages in sequence.

## Interface Convention

Each script should support:

- --manifest configs/run_manifest.json
- --forest-def configs/forest_definition.yaml
- --output-prefix runs/<run_id>

## Logging

Write structured logs with:

- run_id
- tile_id
- stage
- duration_seconds
- warnings

## Run Commands

All scripts require:

- --manifest
- --forest-def
- --aoi-geojson

Example sequence:

1. source /Users/server/projects/sentinel-monthly-forest-cover/.venv/bin/activate
2. python /Users/server/projects/sentinel-monthly-forest-cover/scripts/build_monthly_composites.py --manifest /Users/server/projects/sentinel-monthly-forest-cover/configs/run_manifest.example.json --forest-def /Users/server/projects/sentinel-monthly-forest-cover/configs/forest_definition.example.yaml --aoi-geojson /Users/server/projects/sentinel-monthly-forest-cover/configs/aoi.example.geojson
3. python /Users/server/projects/sentinel-monthly-forest-cover/scripts/compute_ndvi_anomaly.py --manifest /Users/server/projects/sentinel-monthly-forest-cover/configs/run_manifest.example.json --forest-def /Users/server/projects/sentinel-monthly-forest-cover/configs/forest_definition.example.yaml --aoi-geojson /Users/server/projects/sentinel-monthly-forest-cover/configs/aoi.example.geojson
4. python /Users/server/projects/sentinel-monthly-forest-cover/scripts/estimate_loss_area.py --manifest /Users/server/projects/sentinel-monthly-forest-cover/configs/run_manifest.example.json --forest-def /Users/server/projects/sentinel-monthly-forest-cover/configs/forest_definition.example.yaml --aoi-geojson /Users/server/projects/sentinel-monthly-forest-cover/configs/aoi.example.geojson
5. python /Users/server/projects/sentinel-monthly-forest-cover/scripts/export_reporting_artifacts.py --manifest /Users/server/projects/sentinel-monthly-forest-cover/configs/run_manifest.example.json --forest-def /Users/server/projects/sentinel-monthly-forest-cover/configs/forest_definition.example.yaml --aoi-geojson /Users/server/projects/sentinel-monthly-forest-cover/configs/aoi.example.geojson

Single-command orchestrator:

1. python /Users/server/projects/sentinel-monthly-forest-cover/scripts/run_pipeline.py --manifest /Users/server/projects/sentinel-monthly-forest-cover/configs/run_manifest.example.json --forest-def /Users/server/projects/sentinel-monthly-forest-cover/configs/forest_definition.example.yaml --aoi-geojson /Users/server/projects/sentinel-monthly-forest-cover/configs/aoi.example.geojson

## Per-Tile Outputs

- composites_tiles.json
- ndvi_anomaly_tiles.json
- loss_area_tiles.json
- loss_area_tiles.csv

## Sentinel-1 Confirmation

Configure s1_confirmation in run_manifest to enable SAR-based confirmation and optical/SAR confidence fusion.
