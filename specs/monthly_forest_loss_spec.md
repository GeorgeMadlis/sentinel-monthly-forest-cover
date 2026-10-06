# Monthly Forest Loss Estimation Spec

## Objective
Estimate monthly disturbed forest area from NDVI anomaly, constrained by forest mask and quality filters.

## Inputs

1. AOI geometry
2. Reference period image set
3. Current month image set
4. Forest mask image
5. Threshold parameters
6. Optional AOI tiling parameters
7. Optional Sentinel-1 confirmation parameters

## Definitions

1. NDVI
- NDVI = (NIR - RED) / (NIR + RED)

2. Baseline statistics
- mu_ref: baseline NDVI mean
- sigma_ref: baseline NDVI standard deviation

3. Anomaly score
- a = NDVI_current - mu_ref

4. Disturbance mask
- d = 1 if a < tau, else 0
- tau is threshold, e.g. tau = -k * sigma_ref or fixed percentile

5. Optional Sentinel-1 confirmation
- Build month-level VV/VH reference and current composites.
- Compute delta bands:
	- delta_vv = VV_current - VV_reference
	- delta_vh = VH_current - VH_reference
- Confirm disturbance if both decreases pass configured thresholds.

6. Confidence fusion
- optical_conf from valid-pixel and cloud diagnostics.
- s1_conf from Sentinel-1 confirmation ratio.
- fused_conf = w_optical * optical_conf + w_s1 * s1_conf

## Area Estimation

1. Disturbed area image
- A_px = d * pixel_area

2. Hectares
- disturbed_ha = sum(A_px) / 10000

## Quality Rules

1. Minimum valid pixel ratio per tile.
2. Maximum cloud fraction threshold.
3. Minimum connected component size.

## Output Schema

- run_id
- tile_id
- month
- disturbed_ha
- valid_pixel_ratio
- cloud_fraction
- confidence_score
- threshold_value
- dataset_versions

Per-tile outputs also include:

- tile_id
- s1_confirmation_enabled

## Caveats

1. Monthly results are disturbance confirmations, not definitive legal deforestation events.
2. Annual reconciliation against independent references is required.
3. Sentinel-1 confirmation can reduce false positives but may miss subtle optical-only disturbances.
