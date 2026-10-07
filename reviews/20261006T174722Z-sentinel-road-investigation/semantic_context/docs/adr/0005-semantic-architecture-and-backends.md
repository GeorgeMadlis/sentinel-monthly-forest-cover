# ADR 0005: Semantic authority and execution backends

- **Status:** Accepted (task-supplied architecture policy; empirical methods remain candidates)
- **Date:** 2026-10-06
- **Deciders:** Repository task owner
- **Supersedes:** ADR 0001 default backend policy

## Context and decision

Forest Cover Lab is the scientific, governance and semantic authority for forest-cover
work. Human-maintained Markdown/YAML concepts describe applications, scientific questions,
methods, observation requirements, measurements, dataset families, access mechanisms,
processing capabilities, workflows, validation and bounded claims. Generated JSON is a
rebuildable index. Live catalogues hold scenes; downstream software executes methods;
run manifests and evidence hold execution provenance. No graph database is required.

Regional/country-scale production and commercial-compatible execution should prefer
open, local, cloud-neutral Python tooling: GDAL, Rasterio, rioxarray/xarray, GeoPandas,
Shapely, PyProj, DuckDB Spatial, STAC clients and COG/GeoParquet access. Use Dask where
scale requires it. Production scientific methods must not depend on Google Earth Engine.
These are backend policy choices, not empirical endorsements of an algorithm or legal
assertions about any provider's license.

GEE may remain an example implementation, research/reference backend, demonstration of
equivalent calculations, or optional backend for very large/global analyses when its
licensing and terms are appropriate. It is optional in packaging. Backend selection
must be separate from method selection and recorded in provenance. Existing GEE-specific
v1/v2/v3 acquisition descriptions now describe reference implementation routes; their
scientific definitions, thresholds, uncertainty and non-claims remain in force.

## Seasonal proposal

The corpus adds candidate matched-season interannual and moving-window concepts:
reference years contain matched seasonal windows; the target year has corresponding
windows; a declared mean, median or other aggregation is applied; comparison is
current minus reference using optical and/or SAR evidence. Window alignment, minimum
coverage, missingness, sensor compatibility and decision rules must be configured and
validated. A moving mean is not universally preferred. This proposal supplies no
accuracy claim and no validated threshold; promotion requires scientific review.

## Consequences and acceptance

- Stable DS identifiers and existing inventory semantics remain unchanged.
- Tool capability facts cite official documentation and do not imply method validity.
- Candidate relationships are exported separately and cannot become authoritative through
  a workflow run. Contract transcriptions identify their basis explicitly.
- Methods can have several partial implementations; IMPLEMENTS does not certify equivalence.
- Local graph checks, downstream descriptor checks and compatible provenance extensions
  govern reproducibility without installing execution software.
- ADR 0001 remains historical; this decision supersedes its default-platform policy.

References: `knowledge/README.md`, `graph/README.md`, `docs/downstream_repos.md`,
`governance/knowledge_promotion.md`, `validate/semantic_provenance.md`.

## Alternatives considered

A hosted graph database is deferred: a derived local JSON graph supports the initial
contracts with less operational burden. Dataset-only application links are rejected because
they hide observation semantics and prevent principled substitution. A mandatory GEE backend
is rejected by the supplied production policy. Automatic promotion from AI extraction or
individual runs is rejected because syntax and execution success do not establish science.
