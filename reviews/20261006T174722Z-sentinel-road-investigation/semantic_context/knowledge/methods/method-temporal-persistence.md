---
id: method:temporal-persistence
type: method
title: Temporal persistence
version: '1.0'
status: active
updated: '2026-10-06'
review_after: '2027-04-06'
sources: &id001
- specs/v2_monthly_confirmation.md
relations:
- type: REQUIRES_OBSERVATION
  target: observation:temporal-persistence
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

# Temporal persistence

Require configured consecutive-period conditions (v2 default N=2); declare treatment of missingness and focal-month attribution.
