---
id: method:moving-window-comparison
type: method
title: Moving-window comparison
version: '1.0'
status: candidate
updated: '2026-10-06'
review_after: '2027-04-06'
sources: &id001
- docs/adr/0005-semantic-architecture-and-backends.md
relations:
- type: REQUIRES_OBSERVATION
  target: observation:temporal-persistence
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
- type: REQUIRES_CAPABILITY
  target: capability:labeled-array-aggregation
  status: candidate
  sources: *id001
parameters:
  reference_years: explicit list
  target_year: declared year
  seasonal_windows: matched reference/target windows
  aggregation: mean | median | another declared operator
  window_width: declared duration
  minimum_observations: configured
  missingness: configured
  decision_rule: configured and validated
---

# Moving-window comparison

Aggregate declared moving windows and compare with matched reference windows. Mean, median or another declared operator are parameters, not a universal preference. Edge handling, minimum observations and missingness must be explicit.
