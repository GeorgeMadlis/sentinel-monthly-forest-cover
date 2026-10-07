---
id: access:live-catalogue
type: access
title: Live observation catalogue
version: '1.0'
status: active
updated: '2026-10-06'
review_after: '2027-04-06'
sources: &id001
- docs/adr/0005-semantic-architecture-and-backends.md
relations:
- type: REQUIRES_CAPABILITY
  target: capability:spatial-search
  status: candidate
  sources: *id001
- type: REQUIRES_CAPABILITY
  target: capability:temporal-search
  status: candidate
  sources: *id001
- type: REQUIRES_CAPABILITY
  target: capability:metadata-filtering
  status: candidate
  sources: *id001
---

# Live observation catalogue

Query STAC, GeoParquet or provider services at run time. Record query, version, timestamps and actual selected scene identifiers in run evidence, never the semantic corpus.
