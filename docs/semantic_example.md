# End-to-end semantic example: seasonal S1/S2 comparison

**Question.** Detect possible seasonal forest disturbance for an AOI by comparing
June–August 2026 against the equivalent periods in 2024 and 2025.

**Constraints.** Sentinel-1 and Sentinel-2; 30-day moving windows with a 10-day step;
regional/local Python backend; no Google Earth Engine.

`configs/workflow.example.yaml` encodes exactly these constraints. Resolve its reasoning path
against the pinned Forest Cover Lab graph without opening any catalogue or raster:

```sh
.venv/bin/python scripts/explain_semantic_path.py --config configs/workflow.example.yaml \
  --lab ../forest-cover-lab
```

The command fails if the Lab graph revision differs from `workflow.yaml`, if the application
or any dataset/tool ID is unresolved, if a selected method is not registered as implemented by
the workflow, or if a configured dataset satisfies no required observation.

## Reasoning path (from the command output)

| Step | Resolved concepts | Lab status |
|---|---|---|
| Application | `application:seasonal-forest-change-monitoring` → `question:seasonal-forest-change-monitoring` | candidate |
| Scientific method | `method:matched-season-interannual-comparison`, which uses `method:moving-window-comparison` | candidate |
| Feature methods selected by configuration | `method:ndvi-anomaly` (NDVI present), `method:s1-backscatter-confirmation` (SAR present) | candidate / active |
| Observation requirements | optical vegetation state, SAR backscatter state, forest-cover change; moving-window also lists temporal persistence and S1 confirmation lists disturbance confirmation (neither is produced — see divergences) | edges candidate/validated |
| Datasets | optical state → `DS-0002` Sentinel-2 L2A; SAR state → `DS-0003` Sentinel-1 GRD; forest baseline gate → user-declared `DS-0001` mask | validated observation edges |
| Access | `DS-0002` via `access:live-catalogue` (STAC provider); `DS-0003` via a user-supplied local inventory of preprocessed scenes; `access:gee-asset` is never selected | live-catalogue edges are candidate |
| Tools/capabilities | `tool:stac-client` (spatial/temporal search, metadata filtering), `tool:rasterio` (raster read, windowed IO, raster mask, reprojection), `tool:pyproj` (coordinate transformation), `tool:shapely` (geometry predicates) | validated CAN edges |
| Workflow | `workflow:sentinel-monthly-forest-cover`, implementation 2.0.0, declaration status `declared` with explicit divergences | candidate IMPLEMENTS edges |
| Configuration | `local-python`, EPSG:6933 at 20 m, 256-pixel tiles; `matched-season-moving-window`, `calendar-date` alignment, 7 windows from `[2026-06-01, 2026-07-01)` to `[2026-07-31, 2026-08-30)`, each with two aligned reference windows; median per period, period-composite reference statistics; `optical_and_sar` fusion | run parameters, not canonical defaults |

Sensor roles stay distinct: Sentinel-2 supplies optical NDVI/NDMI/NBR features and Sentinel-1
supplies VV/VH backscatter features. Neither is treated as a forest-loss detector on its own;
both become per-sensor candidates, agreement/disagreement layers are retained, and the
combined decision requires both sensors per pixel (pixels lacking either remain nodata).

## Expected evidence artifacts

Per window `wNNNN/`: `<feature>_{current,reference,reference_std,current_count,reference_count,change}.tif`,
`optical_candidate.tif`, `sar_candidate.tif`, `agreement.tif`, `disagreement.tif`,
`fused_candidate.tif`, `disturbance.tif`, `qa.png`. Per run: `config_snapshot.json`,
`observation_inventory.json` (live query, filters, timestamps and the scene IDs actually
selected), tile/window summaries (`loss_area_tiles.*`, `loss_area_summary.*`, `metrics.json`),
`report.md`, `final_map.html` and `run_manifest.json`. The manifest's `semantic_provenance`
records workflow ID/version, method IDs/versions, concept IDs (application, observations,
validation, non-claim), dataset IDs, tool IDs/versions and the Lab commit plus graph revision;
`selected_item_ids` and `observation_inventory.json` record actual observations. Scenes are
never written to the Lab corpus.

## Synthetic execution

`tests/test_workflow.py::LocalWorkflowTests::test_seasonal_s1_s2_semantic_example_end_to_end`
runs the same temporal configuration on the tiny synthetic fixture (`tests/fixtures.py`),
validates the resulting manifest against the local Lab graph and checks the trace. Fixture
observations exist only in June, so later windows have zero selected items and remain nodata
rather than being reported as absence. The fixture is synthetic; its areas are semantic test
values, not scientific results, and no satellite accuracy is implied.
