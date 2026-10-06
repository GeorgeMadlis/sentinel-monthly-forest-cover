# Monthly Workflow

## Step 1: Prepare Run Inputs

1. Copy configs/run_manifest.example.json to configs/run_manifest.json.
2. Copy configs/forest_definition.example.yaml to configs/forest_definition.yaml.
3. Set run month, AOI, and output destination.

## Step 2: Build Reference Baseline

1. Select baseline period using manifest rules.
2. Build cloud-screened Sentinel-2 composites.
3. Compute NDVI baseline statistics.

## Step 3: Build Current Month Composite

1. Load current month Sentinel-2 data.
2. Apply cloud-probability masking.
3. Build median/percentile composite.

## Step 4: Compute Disturbance Signal

1. Compute NDVI anomaly relative to baseline.
2. Gate by forest definition mask.
3. Apply anomaly threshold and cleanup rules.

## Step 5: Estimate Area

1. Multiply disturbance mask by pixel area.
2. Aggregate by tile and AOI.
3. Save hectares and uncertainty metrics.

## Step 6: Export Evidence

1. Export tile summaries and AOI rollup.
2. Export quicklook maps (RGB + disturbance mask).
3. Save run metadata and config snapshot.

## Step 7: Review

1. Validate low-confidence tiles.
2. Compare against annual reference layer for coherence checks.
3. Mark run status as provisional or accepted.
