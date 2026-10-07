---
id: method:matched-season-interannual-comparison
type: method
title: Matched-season interannual comparison
version: '1.0'
status: candidate
updated: '2026-10-06'
review_after: '2027-04-06'
sources: &id001
- docs/adr/0005-semantic-architecture-and-backends.md
relations:
- type: REQUIRES_OBSERVATION
  target: observation:optical-vegetation-state
  status: candidate
  sources: *id001
- type: REQUIRES_OBSERVATION
  target: observation:sar-backscatter-state
  status: candidate
  sources: *id001
- type: REQUIRES_OBSERVATION
  target: observation:forest-cover-change
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
- type: USES_METHOD
  target: method:moving-window-comparison
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
  input_selection: optical | SAR | both, explicitly declared; listed observation edges
    are alternatives for sensor inputs
---

# Matched-season interannual comparison

Compare corresponding seasonal windows in reference years and target year using optical and/or SAR. Align season, quality, coverage and sensor processing before calculating current minus reference. Decision rules require explicit configuration and validation. No performance superiority is asserted.
