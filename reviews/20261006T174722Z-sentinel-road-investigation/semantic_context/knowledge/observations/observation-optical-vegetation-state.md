---
id: observation:optical-vegetation-state
type: observation
title: Optical vegetation state
version: '1.0'
status: active
updated: '2026-10-06'
review_after: '2027-04-06'
sources: &id001
- specs/v2_monthly_confirmation.md
relations:
- type: MEASURED_AS
  target: measurement:ndvi
  status: validated
  sources: *id001
  review:
    by: repository-contract-transcription
    date: '2026-10-06'
    basis: Traceable transcription of the cited contract; no empirical validation
      implied.
- type: CAN_BE_OBSERVED_BY
  target: DS-0002
  status: validated
  sources: *id001
  review:
    by: repository-contract-transcription
    date: '2026-10-06'
    basis: Traceable transcription of the cited contract; no empirical validation
      implied.
---

# Optical vegetation state

Quality-masked optical evidence; clouds, shadows and phenology limit interpretation.
