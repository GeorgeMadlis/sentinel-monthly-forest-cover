---
id: method:ndvi-anomaly
type: method
title: NDVI anomaly
version: '1.0'
status: candidate
updated: '2026-10-06'
review_after: '2027-04-06'
sources: &id001
- specs/v2_monthly_confirmation.md
relations:
- type: REQUIRES_OBSERVATION
  target: observation:optical-vegetation-state
  status: candidate
  sources: *id001
- type: REQUIRES_VALIDATION
  target: validation:forest-evidence
  status: candidate
  sources: *id001
- type: BOUNDED_BY
  target: claim:monthly-non-truth
  status: candidate
  sources: *id001
parameters:
  decision_rule: configured; validate for target context
---

# NDVI anomaly

Compare NDVI with a declared reference under quality masks. Reference, anomaly threshold and confounder handling need validation; v2 specifies indicators but not an anomaly classifier.
