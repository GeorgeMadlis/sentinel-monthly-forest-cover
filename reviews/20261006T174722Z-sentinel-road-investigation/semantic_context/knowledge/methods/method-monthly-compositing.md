---
id: method:monthly-compositing
type: method
title: Monthly compositing
version: '1.0'
status: active
updated: '2026-10-06'
review_after: '2027-04-06'
sources: &id001
- specs/v2_monthly_confirmation.md
relations:
- type: REQUIRES_OBSERVATION
  target: observation:optical-vegetation-state
  status: validated
  sources: *id001
  review:
    by: repository-contract-transcription
    date: '2026-10-06'
    basis: Traceable transcription of the cited contract; no empirical validation
      implied.
- type: REQUIRES_OBSERVATION
  target: observation:sar-backscatter-state
  status: validated
  sources: *id001
  review:
    by: repository-contract-transcription
    date: '2026-10-06'
    basis: Traceable transcription of the cited contract; no empirical validation
      implied.
- type: REQUIRES_VALIDATION
  target: validation:forest-evidence
  status: validated
  sources: *id001
  review:
    by: repository-contract-transcription
    date: '2026-10-06'
    basis: Traceable transcription of the cited contract; no empirical validation
      implied.
- type: BOUNDED_BY
  target: claim:monthly-non-truth
  status: validated
  sources: *id001
  review:
    by: repository-contract-transcription
    date: '2026-10-06'
    basis: Traceable transcription of the cited contract; no empirical validation
      implied.
- type: REQUIRES_CAPABILITY
  target: capability:labeled-array-aggregation
  status: candidate
  sources: *id001
parameters:
  decision_rule: configured; validate for target context
---

# Monthly compositing

Quality-aware calendar-month composites. Existing v2 reference uses optical median and SAR mean; record coverage and gaps.
