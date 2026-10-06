# Sentinel Monthly Forest Cover

Operational architecture for monthly forest-loss area estimation using Sentinel-2 NDVI disturbance signals, with optional Sentinel-1 SAR confirmation.

## Repository Goal
Build a reproducible monthly pipeline that:

1. Ingests AOI definitions and run manifests.
2. Computes monthly disturbance candidates from NDVI anomaly.
3. Produces tile-level and AOI-level area summaries with uncertainty notes.
4. Exports evidence artifacts for review.

## Initial Architecture Files

- docs/architecture.md: System architecture and component boundaries.
- docs/monthly_workflow.md: End-to-end monthly run steps.
- docs/dataset_contract.md: Input dataset IDs and update policy.
- specs/monthly_forest_loss_spec.md: Technical specification and formulas.
- configs/run_manifest.example.json: Example run contract.
- configs/forest_definition.example.yaml: Example forest definition contract.
- scripts/README.md: Script inventory and implementation plan.

## Suggested First Implementation Order

1. Implement script: scripts/build_monthly_composites.py
2. Implement script: scripts/compute_ndvi_anomaly.py
3. Implement script: scripts/estimate_loss_area.py
4. Implement script: scripts/export_reporting_artifacts.py

## Processing Position

This repository estimates monthly forest disturbance confirmations. Final policy-grade attribution should include external QA and annual reconciliation.
