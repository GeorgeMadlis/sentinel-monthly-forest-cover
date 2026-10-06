# Architecture

The six boundaries remain configuration → data access → features/composites →
disturbance decision → area estimation → reporting/evidence. Forest Cover Lab owns
scientific definitions. `workflow.yaml` pins its revision and graph, references actual
method/observation/DS IDs, and declares partial coverage rather than audited equivalence.

| Boundary | Implementation | Durable evidence |
|---|---|---|
| Configuration | `forest_change/config.py`, `temporal.py`, workflow schema | config/forest-definition/AOI snapshot, aligned half-open windows |
| Discovery | `providers.py`: ObservationProvider, LocalRasterProvider, STACProvider | observation inventory with filters, geometry hash, item/asset IDs, timestamps, available checksums/ETags |
| Features/composites | `algorithms.py`, `pipeline.py`, `raster.py` | per-feature current, reference mean/std and valid counts; change rasters |
| Decision | pure threshold/forest gate/fusion/component functions | optical/SAR candidates, agreement, disagreement, fused candidates and cleaned disturbance |
| Area | equal-area grid determinant in square metres converted to hectares | per-tile/per-window CSV/JSON/GeoJSON and metrics |
| Reporting | bounded QA thumbnails and HTML evidence viewer | report, manifest, output SHA-256 checksums |

`ObservationProvider.search/open_asset/describe_source` separates discovery and asset
access from numerical calculations. Future static/GeoParquet catalogues can implement
this interface without modifying algorithms. The local inventory is user input, not a
repository scene database. STAC discovery runs live; an inventory is archived per run.
STAC collection/asset names and calibration are explicitly mapped by the user; no
provider-specific scene URL or dataset edition is guessed.

An AOI union in EPSG:4326 is transformed onto a snapped equal-area grid. Rasterio
WarpedVRT reads/reprojects only requested windows; categorical masks use nearest
neighbour, continuous bands bilinear. GeoTIFF outputs are compressed and tiled,
not claimed as COG-validated outputs. Remote COG URLs allow GDAL range reads when
the server supports them. Source block layout still determines actual read volume.
Country rasters remain on disk; working memory scales with tile pixels × scene count ×
features and reference-period count. A configurable observation cap fails explicitly.
Median requires tile-sized temporal stacks. No Dask or distributed service is needed.

Minimum component filtering uses 8-connected labels on halos of N−1 pixels for a
minimum of N pixels, then crops to the tile core. Components below N cannot reach
outside that halo; components reaching outside necessarily meet N. Tile-size equivalence
is tested. Halos exceeding tile size are rejected to bound memory. This is not general
morphological smoothing. AOI boundary integration uses pixel centres and may vary with
resolution; antimeridian-spanning AOIs must be split first.

The local backend supports candidate screening, not all v2 confirmed-forest rules.
Temporal persistence, terrain flattening, speckle treatment and national validation
remain external/not implemented. Persistence periods other than one are rejected.
Missing optical/SAR evidence remains nodata; S1-only use requires explicit configuration.
No automatic fallback or legality/attribution inference occurs. Weighted fusion is a
weighted candidate-vote score, not a calibrated confidence probability.
