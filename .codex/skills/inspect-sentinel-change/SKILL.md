---
name: inspect-sentinel-change
description: Visually compare Sentinel NDVI and NDVI-plus-SAR maps, investigate road-like changes, and run reproducible threshold sensitivity experiments on existing run rasters.
---

# Inspect and test Sentinel change

Read [investigation contract](references/investigation-contract.md) and [threshold protocol](references/threshold-protocol.md).

1. Inventory RUN and verify manifest/output hashes, dates, calibration, nodata, CRS, grids and anomaly formulas. Read docs/sigma_sar_comparison.md and forest_change/sigma_sar_map.py plus algorithm/report modules. Discover filenames; do not assume a described artifact exists.
2. Open comparison.html and inspect the four maps and raw reference/target RGB with overlays OFF first. Expected map directories are maps_original (fixed optical), maps_fixed_sar, maps_ndvi_sigma and maps (sigma+SAR); verify actual thresholds. Capture identical bounds/zoom/stretch with overlay off/on for each. Inspect source PNGs and georeferenced crops at native resolution. Do not identify a road from the red overlay alone.
3. Delineate every candidate linear feature and representative unchanged/control areas in rois.geojson. Measure projected length, apparent width and width in source pixels; record ambiguity below effective resolution. Check registration using stable landmarks before differencing. Record clouds, shadow, SCL masks, count/std rasters, resampling and mixed pixels. Do not silently shift imagery.
4. Isolate radar using fixed vs fixed+SAR, and sigma vs sigma+SAR. Do not interpret fixed-vs-sigma differences as radar effects because sigma changes the optical reference. On common valid support, compute four categories: both, optical-only, radar-only, neither. Report sensor-unavailable separately, denominator, area and per-ROI counts. AND reduces candidates by construction, not proven false positives. Investigate the continuous VV/VH differences where the apparent road is removed; a narrow road may fail a drop-only radar test. Do not assume SAR must decrease for a road.
5. Execute the robust/sensitivity experiment in the threshold protocol where source stacks exist. Reuse repository access/calibration/grids and tiled IO. First reproduce baseline counts. Preserve original outputs; create new experiment manifests, masks and comparison layers. Inspect every new result visually. A successful numeric test is not accuracy validation.
6. Write inspect/visual_findings.md, rois.geojson, inspect/roi_metrics.csv, inspect/contact_sheet.png, inspect/threshold_experiments.json, a portable comparison HTML under inspect/maps/ if tooling permits (copy map assets, no links into RUN), and investigation.json; keep executed scripts in scripts/ and experiment outputs in inspect/experiments/. Include exact commands/tests and source hashes. Run the review site builder from the contract. Stop short of road confirmation; emit explicit questions for the next two skills.
