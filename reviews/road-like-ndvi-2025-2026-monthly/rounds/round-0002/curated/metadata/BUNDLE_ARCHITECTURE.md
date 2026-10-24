# Versioned evidence-bundle architecture and contract

## Recommended three-layer boundary

**Lab:** `forest-cover-lab` is the canonical role, scientific-method and governance registry, not a storage location for processed scene rasters. No automatic promotions.

**Sentinel working evidence:** `sentinel-monthly-forest-cover/reviews/road-like-ndvi-2025-2026-monthly/rounds/round-NNNN/` stores the graph, assignments, decisions, actual agent attempts and evidence references for each round. Existing archived review of 2026-10-06 is immutable/read-only as an input. Outputs can live in an associated `runs/` directory referenced by SHA-256 rather than be copied into Git.

**Evidence release archive:** propose a new `GeorgeMadlis/public-bundles` repository for human-approved, small, curated static bundles. This repository was **not** found through the linked GitHub connection; creation/publication is not performed by this package. If your actual `private-bundles` repository exists outside current connector access, it may store unreviewed private drafts; don't treat it as verified or accessible. Public publication is optional and separate from acceptance of working results.

## Bundle convention

`bundles/forest-road-ndvi-aoi-example-2025-2026/round-0001/`

Required release paths:

```text
index.html                       # offline entry, no CDN/no API fetch
report.html                      # human-readable verdict, disputed claims
report.md                        # source manuscript
bundle_manifest.json             # file SHA-256, sources, license and evidence status
metadata/claim_matrix.csv        # proposition-by-ROI results
metadata/disagreements.csv       # retained conflicts and unknowns
metadata/sources.csv             # retrieval/acquisition & lineage
metadata/harness.json            # host/model/loaded files/attempts (privacy safe)
metadata/round.yaml              # frozen approved graph and gates
figures/                         # annotated exported PNGs + source dates
maps/                            # independent offline Leaflet viewers and vendor assets
agents/<id>/plan.md              # plan and approval
agents/<id>/report.md            # observations, failed tests, limits
agents/<id>/execution.json       # actually observed attempts or explicit not_run
inquiry/round-0001.md            # decisions, corrections, unresolved evidence
```

`bundle_manifest.json` must enumerate every included file (except itself), relative path, size and SHA-256; include version, upstream full commit SHAs, AOI geometry digest, data provider/scene IDs, source dates, forest definition/mask status, available labels, review decision, license and actual full list of checks. Validate hashes after ZIP extraction. An external URL or `file://` absolute server path must not be required for local inspection. A link to scientific raw data may be external only if it is clearly nonessential to offline review. Keep raster COGs in read-only object storage or private working directories unless redistribution is licensed and intentionally requested.

The HTML report must allow switching between 2025 and 2026 visual evidence, absolute and relative NDVI signals, candidate masks, road/rail and orthophoto geometry where available. Embed/vend Leaflet JS/CSS/maps just as the existing Sentinel offline reports do; index and report navigation cannot require a network connection. Preserve distinct nodata/unknown visualization. A browser opening `index.html` with `file://` must see its content even when browser `fetch()` of local JSON is prohibited.

## Round semantics

Round 0001 is a **proposal**. Its manifest uses the Lab's schema v1.1 and graph nodes/step plans. `actual_executions` stays empty until actual work. Every new round names its predecessor and what changed: question frame, source edition, dates, method, model, code, hypothesis or verdict. A second round must not mutate round 0001 or silently promote its claims. Synthesis should show trajectory across rounds: candidate -> evidence -> discrepancy -> challenge -> human decision. Distinguish original source artifacts, derived measurements, agent assertions, and human-reviewed interpretations.

## Release gate and reproducibility

The release gate checks that the graph and step plans were approved before attempts, hash manifest passes, linked local HTML/PNGs load offline, licenses permit publication, sensitive paths/tokens/provider-signed URLs are absent, sources and windows are dated, map semantics are accurate, and missing/conflicting evidence appears in the report. A public bundle is a *published record of a bounded inquiry*, not necessarily confirmation of forest loss.
