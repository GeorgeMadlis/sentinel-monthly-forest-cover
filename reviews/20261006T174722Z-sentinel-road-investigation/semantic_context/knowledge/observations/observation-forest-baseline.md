---
id: observation:forest-baseline
type: observation
title: Forest baseline
version: '1.0'
status: active
updated: '2026-10-06'
review_after: '2027-04-06'
sources: &id001
- specs/v1_forest_baseline.md
relations:
- type: MEASURED_AS
  target: measurement:canopy-cover
  status: validated
  sources: *id001
  review:
    by: repository-contract-transcription
    date: '2026-10-06'
    basis: Traceable transcription of the cited contract; no empirical validation
      implied.
- type: CAN_BE_OBSERVED_BY
  target: DS-0001
  status: validated
  sources: *id001
  review:
    by: repository-contract-transcription
    date: '2026-10-06'
    basis: Traceable transcription of the cited contract; no empirical validation
      implied.
---

# Forest baseline

Declared baseline forest extent, definition, MMU, exclusions and nodata; baseline is not a current forest census.
