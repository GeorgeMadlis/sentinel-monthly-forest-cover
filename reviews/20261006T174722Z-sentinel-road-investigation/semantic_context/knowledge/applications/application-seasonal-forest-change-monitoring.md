---
id: application:seasonal-forest-change-monitoring
type: application
title: Seasonal forest-change monitoring
version: '1.0'
status: candidate
updated: '2026-10-06'
review_after: '2027-04-06'
sources: &id001
- docs/adr/0005-semantic-architecture-and-backends.md
relations:
- type: ASKS
  target: question:seasonal-forest-change-monitoring
  status: candidate
  sources: *id001
- type: REQUIRES_OBSERVATION
  target: observation:forest-baseline
  status: candidate
  sources: *id001
- type: REQUIRES_OBSERVATION
  target: observation:optical-vegetation-state
  status: candidate
  sources: *id001
- type: REQUIRES_OBSERVATION
  target: observation:sar-backscatter-state
  status: candidate
  sources: *id001
- type: REQUIRES_OBSERVATION
  target: observation:temporal-persistence
  status: candidate
  sources: *id001
- type: REQUIRES_OBSERVATION
  target: observation:forest-cover-change
  status: candidate
  sources: *id001
- type: REQUIRES_OBSERVATION
  target: observation:disturbance-confirmation
  status: candidate
  sources: *id001
- type: BOUNDED_BY
  target: claim:monthly-non-truth
  status: candidate
  sources: *id001
---

# Seasonal forest-change monitoring

Discovery intent: How do corresponding seasonal observation windows differ between reference and target years? Outputs remain screening or monitoring evidence under explicit validation, uncertainty and forest definitions.
