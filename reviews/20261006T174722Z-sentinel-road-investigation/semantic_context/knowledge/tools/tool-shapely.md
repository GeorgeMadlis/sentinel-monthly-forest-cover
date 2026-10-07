---
id: tool:shapely
type: tool
title: Shapely
version: '1.0'
status: active
updated: '2026-10-06'
review_after: '2027-04-06'
sources: &id001
- https://shapely.readthedocs.io/en/stable/manual.html
relations:
- type: CAN
  target: capability:geometry-predicates
  status: validated
  sources: *id001
  review:
    by: repository-contract-transcription
    date: '2026-10-06'
    basis: Traceable transcription of the cited contract; no empirical validation
      implied.
---

# Shapely

Capabilities describe API-level operations, not scientific correctness. Pin tool versions in runs. Provider/extension support and preprocessing must be checked by the implementation; catalogue filters depend on server conformance.
