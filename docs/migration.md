# Migration from historical GEE runs

Historical scripts are preserved byte-for-byte under `examples/gee/` with their optional
requirements and original flags. Existing `runs/` evidence is unchanged. Production
script names and IO flags remain. Earth Engine credential/project flags fail with an
explicit redirect to examples. The annual-2024 command redirects there too.

A legacy manifest containing only GEE collection IDs cannot supply local rasters: it
fails with a migration message instead of attempting Earth Engine initialization.
Use `configs/workflow.example.yaml`, set calibrated provider assets, explicit optical
quality/SAR preprocessing and an external forest mask. No provider scene URLs or legal
forest transformations can be inferred from old collection names.

The normalizer retains legacy same-month reference-year logic when explicit local
`providers`, `execution`, `forest_mask` **and** observation metadata are added.
Calendar dates migrate to full half-open months. Reference means/std are pooled over
observations, current median stays median, SAR confirmation maps to AND fusion, and
legacy VV/VH thresholds retain current-minus-reference signs. Replace legacy degree
sizes with pixel tile size explicitly; tile IDs/summaries change and a migration note
records this. Unsupported strategies or quality fields require explicit schema 2.0
migration; they are never silently reinterpreted.

The former `max_cloud_fraction` mixed scene cloud filtering and cloud-probability
masking. Local SCL/pre-masked quality differs; remove that field only after declaring
and reviewing the new quality method. Retain its former value in a migration record
outside `threshold`. Sigma cutoffs (`k`), minimum component pixels and valid coverage
thresholds retain their meaning. Optical weighting in old reporting was a coverage score;
new weighted fusion is an explicit candidate-vote rule, so it is not auto-migrated.

Some mathematical formulas match the GEE reference (normalized differences,
current-minus-reference changes, thresholds, gating and hectares). Pixel-level outputs
can differ due to cloud quality, calibration, reprojection, geometry filtering, baseline
weighting, connected components, scale and GEE bestEffort behavior. GEE historically
excluded the final calendar day and combined all SAR orbits; production corrects these
by documented full-month selection and explicit compatible acquisition geometry.
Backend-equivalence tests cover pure semantics and common local/STAC asset reads;
they do not certify satellite-level or GEE execution equivalence.
