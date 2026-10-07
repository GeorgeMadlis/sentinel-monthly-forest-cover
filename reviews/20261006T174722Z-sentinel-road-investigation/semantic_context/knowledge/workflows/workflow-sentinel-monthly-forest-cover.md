---
id: workflow:sentinel-monthly-forest-cover
type: workflow
title: sentinel-monthly-forest-cover
version: '1.1'
status: candidate
updated: '2026-10-06'
review_after: '2027-04-06'
sources: &id001
- docs/downstream_repos.md
relations:
- type: IMPLEMENTS
  target: method:ndvi-anomaly
  status: candidate
  sources: *id001
  scope: Declared by sentinel-monthly-forest-cover 2.0.0 descriptor; partial, equivalence
    not audited.
- type: IMPLEMENTS
  target: method:s1-backscatter-confirmation
  status: candidate
  sources: *id001
  scope: Declared by sentinel-monthly-forest-cover 2.0.0 descriptor; partial, equivalence
    not audited.
- type: IMPLEMENTS
  target: method:monthly-compositing
  status: candidate
  sources: *id001
  scope: Declared by sentinel-monthly-forest-cover 2.0.0 descriptor; partial, equivalence
    not audited.
- type: IMPLEMENTS
  target: method:moving-window-comparison
  status: candidate
  sources: *id001
  scope: Declared by sentinel-monthly-forest-cover 2.0.0 descriptor; partial, equivalence
    not audited.
- type: IMPLEMENTS
  target: method:matched-season-interannual-comparison
  status: candidate
  sources: *id001
  scope: Declared by sentinel-monthly-forest-cover 2.0.0 descriptor; partial, equivalence
    not audited.
- type: IMPLEMENTS
  target: method:temporal-persistence
  status: candidate
  sources: *id001
  scope: Proposed target contract only; not implemented by sentinel-monthly-forest-cover 2.0.0.
    Persistence periods above one are rejected.
- type: CONSUMES
  target: DS-0002
  status: candidate
  sources: *id001
  scope: Declared by sentinel-monthly-forest-cover 2.0.0 descriptor; partial, equivalence
    not audited.
- type: CONSUMES
  target: DS-0003
  status: candidate
  sources: *id001
  scope: Declared by sentinel-monthly-forest-cover 2.0.0 descriptor; partial, equivalence
    not audited.
- type: REQUIRES_OBSERVATION
  target: observation:forest-baseline
  status: candidate
  sources: *id001
  scope: Declared by sentinel-monthly-forest-cover 2.0.0 descriptor; partial, equivalence
    not audited.
- type: REQUIRES_OBSERVATION
  target: observation:optical-vegetation-state
  status: candidate
  sources: *id001
  scope: Declared by sentinel-monthly-forest-cover 2.0.0 descriptor; partial, equivalence
    not audited.
- type: REQUIRES_OBSERVATION
  target: observation:sar-backscatter-state
  status: candidate
  sources: *id001
  scope: Declared by sentinel-monthly-forest-cover 2.0.0 descriptor; partial, equivalence
    not audited.
- type: REQUIRES_OBSERVATION
  target: observation:forest-cover-change
  status: candidate
  sources: *id001
  scope: Declared by sentinel-monthly-forest-cover 2.0.0 descriptor; partial, equivalence
    not audited.
- type: REQUIRES_OBSERVATION
  target: observation:temporal-persistence
  status: candidate
  sources: *id001
  scope: Proposed target contract only; not implemented by sentinel-monthly-forest-cover 2.0.0.
- type: REQUIRES_OBSERVATION
  target: observation:disturbance-confirmation
  status: candidate
  sources: *id001
  scope: Proposed target contract only; not implemented by sentinel-monthly-forest-cover 2.0.0.
- type: USES_TOOL
  target: tool:stac-client
  status: candidate
  sources: *id001
  scope: Declared by sentinel-monthly-forest-cover 2.0.0 descriptor; partial, equivalence
    not audited.
- type: USES_TOOL
  target: tool:rasterio
  status: candidate
  sources: *id001
  scope: Declared by sentinel-monthly-forest-cover 2.0.0 descriptor; partial, equivalence
    not audited.
- type: USES_TOOL
  target: tool:pyproj
  status: candidate
  sources: *id001
  scope: Declared by sentinel-monthly-forest-cover 2.0.0 descriptor; partial, equivalence
    not audited.
- type: USES_TOOL
  target: tool:shapely
  status: candidate
  sources: *id001
  scope: Declared by sentinel-monthly-forest-cover 2.0.0 descriptor; partial, equivalence
    not audited.
- type: USES_TOOL
  target: tool:xarray
  status: candidate
  sources: *id001
  scope: Proposed target contract only; not implemented by sentinel-monthly-forest-cover 2.0.0.
    Temporal aggregation uses NumPy arrays.
- type: REQUIRES_CAPABILITY
  target: capability:spatial-search
  status: candidate
  sources: *id001
  scope: Declared by sentinel-monthly-forest-cover 2.0.0 descriptor; partial, equivalence
    not audited.
- type: REQUIRES_CAPABILITY
  target: capability:temporal-search
  status: candidate
  sources: *id001
  scope: Declared by sentinel-monthly-forest-cover 2.0.0 descriptor; partial, equivalence
    not audited.
- type: REQUIRES_CAPABILITY
  target: capability:metadata-filtering
  status: candidate
  sources: *id001
  scope: Declared by sentinel-monthly-forest-cover 2.0.0 descriptor; partial, equivalence
    not audited.
- type: REQUIRES_CAPABILITY
  target: capability:raster-read
  status: candidate
  sources: *id001
  scope: Declared by sentinel-monthly-forest-cover 2.0.0 descriptor; partial, equivalence
    not audited.
- type: REQUIRES_CAPABILITY
  target: capability:windowed-io
  status: candidate
  sources: *id001
  scope: Declared by sentinel-monthly-forest-cover 2.0.0 descriptor; partial, equivalence
    not audited.
- type: REQUIRES_CAPABILITY
  target: capability:raster-mask
  status: candidate
  sources: *id001
  scope: Declared by sentinel-monthly-forest-cover 2.0.0 descriptor; partial, equivalence
    not audited.
- type: REQUIRES_CAPABILITY
  target: capability:reprojection
  status: candidate
  sources: *id001
  scope: Declared by sentinel-monthly-forest-cover 2.0.0 descriptor; partial, equivalence
    not audited.
- type: REQUIRES_CAPABILITY
  target: capability:coordinate-transformation
  status: candidate
  sources: *id001
  scope: Declared by sentinel-monthly-forest-cover 2.0.0 descriptor; partial, equivalence
    not audited.
- type: REQUIRES_CAPABILITY
  target: capability:geometry-predicates
  status: candidate
  sources: *id001
  scope: Declared by sentinel-monthly-forest-cover 2.0.0 descriptor; partial, equivalence
    not audited.
- type: REQUIRES_CAPABILITY
  target: capability:labeled-array-aggregation
  status: candidate
  sources: *id001
  scope: Proposed target contract only; not implemented by sentinel-monthly-forest-cover 2.0.0.
- type: REQUIRES_VALIDATION
  target: validation:forest-evidence
  status: candidate
  sources: *id001
  scope: Declared by sentinel-monthly-forest-cover 2.0.0 descriptor; partial, equivalence
    not audited.
---

# sentinel-monthly-forest-cover

Executable downstream workflow (an implementation, not a scientific method). It may implement
several methods partially; IMPLEMENTS edges are candidate registrations, not audited scientific
equivalence. Each edge scope distinguishes relationships declared by the pinned implementation
descriptor from proposed target-contract relationships it does not yet implement. Downstream
descriptors and run manifests are validated against these registered relationships, so a new
implementation relationship must be proposed here first. The implementation pins its own
version, declares divergences and must demonstrate validation.
