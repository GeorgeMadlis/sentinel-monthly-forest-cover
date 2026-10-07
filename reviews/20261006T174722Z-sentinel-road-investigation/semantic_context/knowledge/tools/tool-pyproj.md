---
id: tool:pyproj
type: tool
title: PyProj
version: '1.0'
status: active
updated: '2026-10-06'
review_after: '2027-04-06'
sources: &id001
- https://pyproj4.github.io/pyproj/stable/api/transformer.html
relations:
- type: CAN
  target: capability:coordinate-transformation
  status: validated
  sources: *id001
  review:
    by: repository-contract-transcription
    date: '2026-10-06'
    basis: Traceable transcription of the cited contract; no empirical validation
      implied.
---

# PyProj

Capabilities describe API-level operations, not scientific correctness. Pin tool versions in runs. Provider/extension support and preprocessing must be checked by the implementation; catalogue filters depend on server conformance.
