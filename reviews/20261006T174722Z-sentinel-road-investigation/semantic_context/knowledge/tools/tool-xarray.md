---
id: tool:xarray
type: tool
title: xarray
version: '1.0'
status: active
updated: '2026-10-06'
review_after: '2027-04-06'
sources: &id001
- https://docs.xarray.dev/en/stable/user-guide/computation.html
relations:
- type: CAN
  target: capability:labeled-array-aggregation
  status: validated
  sources: *id001
  review:
    by: repository-contract-transcription
    date: '2026-10-06'
    basis: Traceable transcription of the cited contract; no empirical validation
      implied.
---

# xarray

Capabilities describe API-level operations, not scientific correctness. Pin tool versions in runs. Provider/extension support and preprocessing must be checked by the implementation; catalogue filters depend on server conformance.
