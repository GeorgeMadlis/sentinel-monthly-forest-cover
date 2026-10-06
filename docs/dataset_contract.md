# Dataset Contract (2026)

## Mandatory Sources

1. Sentinel-2 surface reflectance
- ID: COPERNICUS/S2_SR_HARMONIZED
- Use: NDVI and RGB composites.

2. Sentinel-2 cloud probability
- ID: COPERNICUS/S2_CLOUD_PROBABILITY
- Use: cloud masking.

3. Forest reference mask
- ID: UMD/hansen/global_forest_change_2024_v1_12
- Use: baseline intact/forest gating.

## Optional Source

1. Sentinel-1 GRD
- ID: COPERNICUS/S1_GRD
- Use: cloud-robust disturbance confirmation.

## Update Policy

1. Dataset IDs must be declared in run manifest output metadata.
2. Deprecated IDs are not allowed in production runs.
3. Year updates must be reviewed each January.

## Validation Checks

1. Confirm each dataset is reachable before run start.
2. Confirm minimum observation count per AOI tile.
3. Record missing-data fraction per tile.
