---
id: method:s1-backscatter-confirmation
type: method
title: Sentinel-1 backscatter confirmation
version: '1.0'
status: active
updated: '2026-10-06'
review_after: '2027-04-06'
sources: &id001
- specs/v2_monthly_confirmation.md
relations:
- type: REQUIRES_OBSERVATION
  target: observation:sar-backscatter-state
  status: validated
  sources: *id001
  review:
    by: repository-contract-transcription
    date: '2026-10-06'
    basis: Traceable transcription of the cited contract; no empirical validation
      implied.
- type: REQUIRES_OBSERVATION
  target: observation:disturbance-confirmation
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
parameters:
  decision_rule: configured; validate for target context
---

# Sentinel-1 backscatter confirmation

Use comparable VV/VH time series as complementary confirmation. v2 requires disagreement flags and preprocessing; backscatter is not uniquely diagnostic of loss.
