---
id: tool:stac-client
type: tool
title: PySTAC Client
version: '1.0'
status: active
updated: '2026-10-06'
review_after: '2027-04-06'
sources: &id001
- https://pystac-client.readthedocs.io/en/stable/usage.html
relations:
- type: CAN
  target: capability:spatial-search
  status: validated
  sources: *id001
  review:
    by: repository-contract-transcription
    date: '2026-10-06'
    basis: Traceable transcription of the cited contract; no empirical validation
      implied.
- type: CAN
  target: capability:temporal-search
  status: validated
  sources: *id001
  review:
    by: repository-contract-transcription
    date: '2026-10-06'
    basis: Traceable transcription of the cited contract; no empirical validation
      implied.
- type: CAN
  target: capability:metadata-filtering
  status: validated
  sources: *id001
  review:
    by: repository-contract-transcription
    date: '2026-10-06'
    basis: Traceable transcription of the cited contract; no empirical validation
      implied.
---

# PySTAC Client

Capabilities describe API-level operations, not scientific correctness. Pin tool versions in runs. Provider/extension support and preprocessing must be checked by the implementation; catalogue filters depend on server conformance.
