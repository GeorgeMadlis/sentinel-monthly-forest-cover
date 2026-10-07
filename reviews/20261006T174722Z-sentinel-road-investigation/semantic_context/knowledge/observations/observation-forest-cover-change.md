---
id: observation:forest-cover-change
type: observation
title: Forest-cover change
version: '1.0'
status: active
updated: '2026-10-06'
review_after: '2027-04-06'
sources: &id001
- specs/v1_forest_baseline.md
relations:
- type: MEASURED_AS
  target: measurement:annual-loss-year
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
- type: CAN_BE_OBSERVED_BY
  target: DS-0007
  status: validated
  sources: *id001
  review:
    by: repository-contract-transcription
    date: '2026-10-06'
    basis: Traceable transcription of the cited contract; no empirical validation
      implied.
---

# Forest-cover change

Change relative to a declared forest definition and reference period; temporal meaning follows the input labels.
