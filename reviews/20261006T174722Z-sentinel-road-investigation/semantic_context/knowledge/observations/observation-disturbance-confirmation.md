---
id: observation:disturbance-confirmation
type: observation
title: Disturbance confirmation
version: '1.0'
status: active
updated: '2026-10-06'
review_after: '2027-04-06'
sources: &id001
- specs/v2_monthly_confirmation.md
relations:
- type: MEASURED_AS
  target: measurement:vv-vh-backscatter
  status: validated
  sources: *id001
  review:
    by: repository-contract-transcription
    date: '2026-10-06'
    basis: Traceable transcription of the cited contract; no empirical validation
      implied.
---

# Disturbance confirmation

Combine temporal and optical/SAR evidence; flag disagreement. Confirmation is conditional on validation, not cause attribution.
