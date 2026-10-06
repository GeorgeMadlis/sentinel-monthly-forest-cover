# Sentinel forest disturbance evidence

A GEE-independent, tiled Sentinel-2 + optional Sentinel-1 workflow for small AOIs,
regions and countries. Scientific governance remains in
[Forest Cover Lab](https://github.com/GeorgeMadlis/forest-cover-lab). This repository
executes provisional disturbance screening and preserves reproducible evidence.

**Disturbance candidates are not legal deforestation, confirmed forest state or causal
loss labels.** Hansen annual loss is not monthly ground truth. Optical signals have
phenology/cloud/fire/agriculture/moisture confounders; SAR depends on moisture,
geometry and terrain. Sensor agreement does not establish cause. External QA and
annual reconciliation remain necessary.

```sh
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/create_synthetic_fixture.py --directory /tmp/forest-demo
.venv/bin/python scripts/run_pipeline.py \
  --manifest /tmp/forest-demo/workflow.yaml \
  --forest-def /tmp/forest-demo/forest.yaml \
  --aoi-geojson /tmp/forest-demo/aoi.geojson
.venv/bin/python -m unittest discover -v
```

The demo is synthetic, requires no credentials or network, and writes evidence to
`/tmp/forest-demo/output`. See `configs/workflow.example.yaml` for real-run configuration.
Local input paths are relative to their configuration/inventory files; output prefixes
are relative to the invocation directory. All production commands use the existing
`--manifest`, `--forest-def`, `--aoi-geojson`, `--output-prefix` flags.

- [Architecture](docs/architecture.md): stages, IO and partial scientific coverage.
- [Workflow](docs/monthly_workflow.md): monthly, moving-window and matched-season modes.
- [Dataset contract](docs/dataset_contract.md): providers, calibration and preprocessing.
- [Migration](docs/migration.md): legacy manifests and retained reference commands.
- [Capability descriptor](workflow.yaml): pinned Lab methods/observations and divergences.
- [Workflow schema](specs/workflow.schema.json): version 2.0 configuration.
- [Validation](docs/validation.md): checks, evidence and remaining limitations.

Historical GEE code and interactive maps remain under `examples/gee/` and `runs/`.
GEE is optional reference code; it is absent from production dependencies. Only the
`local-python` execution backend is implemented. STAC and local-raster are data providers.
