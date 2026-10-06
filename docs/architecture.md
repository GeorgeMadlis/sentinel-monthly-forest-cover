# Architecture

## High-Level Components

1. Configuration Layer
- Inputs:
  - configs/run_manifest.json
  - configs/forest_definition.yaml
- Responsibilities:
  - AOI selection
  - date windows
  - thresholds and runtime options

2. Data Access Layer
- Sources:
  - Sentinel-2 SR Harmonized
  - Sentinel-2 Cloud Probability
  - Hansen GFC (latest)
  - optional Sentinel-1 GRD
- Responsibilities:
  - collection loading
  - filtering by AOI/time/cloud

3. Feature Layer
- Responsibilities:
  - NDVI calculation
  - reference-period baseline statistics
  - current-month anomaly image generation
  - optional SAR change features

4. Disturbance Decision Layer
- Responsibilities:
  - thresholding (z-score or sigma based)
  - forest mask gating
  - morphology cleanup and minimum mapping unit
  - confidence score assignment

5. Area Estimation Layer
- Responsibilities:
  - pixel area integration in hectares
  - tile summary + AOI rollup
  - uncertainty diagnostics

6. Reporting and Evidence Layer
- Outputs:
  - per-tile GeoJSON/Parquet summaries
  - AOI summary table
  - RGB + mask quicklooks
  - run metadata and config snapshot

## Processing Graph

1. Load config and AOI
2. Build reference baseline (N months or same-month climatology)
3. Build current monthly composite
4. Compute NDVI anomaly
5. Apply forest mask + threshold
6. Estimate area and confidence
7. Export tabular + geospatial + visual evidence

## Interfaces (Contract Sketch)

- Baseline output:
  - ndvi_mean_ref, ndvi_std_ref
- Disturbance output:
  - disturbance_mask, anomaly_value
- Area summary output:
  - tile_id, disturbed_ha, confidence_mean, valid_pixel_ratio

## Non-Functional Requirements

1. Reproducibility: run outputs include manifest and dataset IDs.
2. Auditability: every run writes threshold values and data availability stats.
3. Robustness: degraded mode when optical coverage is poor.
4. Scalability: tile-level parallel execution.
