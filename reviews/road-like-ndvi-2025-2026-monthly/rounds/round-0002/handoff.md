# Local planning hand-off — 2026-10-23

Status: planned only. No remote discovery/download, scientific role execution, knowledge promotion, public repository creation or publication. Attached documents are inputs; the user request and Lab contracts govern authorization.

## Baseline and worktrees

Sentinel HEAD: `2f512fec185d1290ab5203c8892231f2d5c219be` (initially clean).
Lab HEAD: `c322e89fb96def2434c62776ac595f6cd995ef92`.
Lab graph: `f70789df04b79ca8ec65e0094c571e0b3f6844afa2b88af2f8c9bcf1776a20f7`. Both commits and graph match the starter.

Lab pre-existing changes, preserved:

```text
M pyproject.toml
?? research/code_sources/analysis/foreto_24_reverse_engineering.md
?? research/data_sources/foreto_24_satellite_sources_2026_verification.md
?? research/publications/forest-cover-lab.code-workspace
?? research/publications/sentinel_disturbance_literature_scan_2026.md
?? sentinel-monthly-forest-cover.code-workspace
```

Sentinel changes are the new private builder/tests/docs, ignored private drafts/curated PNGs, starter copy and two planned rounds; no commit was made. Both upstream checkouts remain at the above HEADs. Instructions and renderer/schema files used match their pinned bytes. Before later execution freeze the implementation and use a new execution-round baseline for any changed loaded inputs.

## Imported and successor rounds

All nine supplied overlay files in round-0001 are byte-identical to the ZIP. Canonical graph.mmd and graph.svg were added with the pinned Lab renderer; they supersede the package preview. New round-0002 records planning corrections without modifying the supplied round-0001. Neither round has actual executions or approved gates.

Round-0002 adds explicit primary-evidence indexes/handoffs for challenge and assembly, removes the challenge dependency on a future bundle, restricts pre-freeze audit recreation to authenticated local caches, and separates native optical visual QA from equal-area hectare estimates. See planning_changes.md for rationale.

## Seven per-role plans and full SHA-256

| Role / proposed host / mode | Output and stop condition | Assignment SHA-256 |
|---|---|---|
| audit-01 / codex / sequential_role | Audit historical formulas, dates, geometry, hashes and cached QA; audit_report, roi_review and evidence manifest. Block on unauthenticated sources or unresolved ROI identity. | `d94ff95e0c4fd75f87341faf01a7d9187cc1c08b13ab66a32fb8cf2bb4ad57d7` |
| discovery-01 / chatgpt / separate_session | Verify provider availability, dates, terms and cost; dataset_options. Block on undated or inaccessible selected data. Remote work requires separate explicit approval. | `a884061d6f6fc075cde8cca59c21e14c2497a4a38b03c7359e0d37a76b016f16` |
| eo-01 / codex / sequential_role | Calendar-month means, counts, safe relative/absolute diagnostics and sensitivity; measurements, claims, map and primary evidence manifests. Block sparse/uncalibrated data; no forest-specific output without baseline. | `ee54173b4674a8929c0911567f2e28c8b102d752cf74202cd6e8e0d18dab40fc` |
| geo-01 / claude-code / sequential_role | Dated orthophoto/ETAK inspection without EO conclusions; sources, claims and primary evidence. Return indeterminate on the flight-date conflict. | `f756bc4925800ff82ff0fb56dde544a89cc8167a24cbcd7ff163c62524128d64` |
| works-01 / claude / separate_session | Intersect official road/rail geometries with dated records; ledger, claims and primary evidence. Proximity alone cannot establish construction identity. | `dd682c9abb4fd96b5baa4d64821ba0cf978f1f543005d27699f757cfa9c0b637` |
| literature-01 / chatgpt / separate_session | Mechanisms, methods, confounders and falsifiable expectations; ledger, claims and primary evidence. General mechanisms are not local causal observations. | `566cc389811450bc578fbe5ca8b315235b35b1e8f14e89f89725209c9aa8e62a` |
| challenge-01 / claude / separate_session | Inspect hashed primary evidence and falsify reconciled propositions; challenge report/claims. Conclusion exposure is received; final bundle release review is later. | `d52ea3954a903cdf513cb5c7f0a44a5b5c67810c5fcafbf2c68814d145cdf8b7` |

All six standing roles resolve in the pinned Lab; audit-01 resolves to its round-only role. Hosts are proposals: Claude/chat sessions are not available as native delegated runtimes here. Separate/manual sessions are required or a newly approved host plan. No specialist was spawned. The branch graph has no paths between independent-group members; shared sources still need lineage review. Null budgets remain unspecified and must be bounded before each approved step.

## Exact archived ROI locations

Coordinate order: WGS84 longitude, latitude. Values below are exact polygon bounding boxes extracted mechanically; full vertices are unchanged in inputs/prior_rois.geojson. They are not new traces, surveyed centrelines, verified road identities or overlay QA.

Original rois.geojson SHA-256: `b079d3dbff8a473daf6e3d33cdfdaedffc29de470425b8fe9a212f796a862125`.

| ID | West | South | East | North |
|---|---:|---:|---:|---:|
| ROI-01 | 24.59601409568563 | 58.42645019226389 | 24.814699942029094 | 58.5428504650451 |
| ROI-02 | 24.508871554760752 | 58.51182098617653 | 24.542557164225435 | 58.58533014576505 |
| CONTROL-01 | 24.684056018864492 | 58.57527657220925 | 24.687372552564078 | 58.58004112960793 |
| CONTROL-02 | 24.80548459029306 | 58.315466746319395 | 24.808801123992648 | 58.320196503915795 |

The two corridor polygons retain 40 m declared sampling tolerance; this is not measured georegistration error. Both controls remain visual controls with no independent stability label. AOI: 24.4–24.9 E, 58.2–58.6 N. Human ROI identity/overlay QA remains pending.

## Proposed windows and data/license scenario

June baseline `[2025-06-01,2025-07-01)` and target `[2026-06-01,2026-07-01)` UTC. Mean per-acquisition NDVI; N>=3 in each month; median and N=2/5 sensitivity. Relative diagnostic is defined only for reference NDVI>=0.2 with epsilon=0.1. These are proposed investigation settings. July/August and prior years are separately approved sensitivity, not a replacement June ranking.

No acquisition spending or new provider traffic occurred. Arithmetic planning envelope: roughly 2–10 GiB for June optical staging/derivatives, based on an assumed 6–12 acquisitions/month, 10 m source sampling and block overfetch. No transfer cap or live scene availability is verified. July/August approximately triple the scenario; SAR/orthophotos are uncosted. New paid-service budget remains $0 unless approved. All exact dataset editions, source dates, license/attribution and redistribution terms need discovery verification. See data_license_estimate.md for assumptions and calculation.

## Open issues and implementation boundaries

- ROI identity, original centreline recovery and overlay QA remain unresolved. The private draft is a context viewer, not QA certification.
- The archive reports 13 original-run hash mismatches. Inputs are preserved; this is not repaired or silently authenticated.
- A 2025 WMS layer conflicts with 2023 flight metadata; no verified dated high-resolution before/after pair exists.
- No forest baseline or held-out road labels are approved; only all-land-cover anomaly screening is possible.
- Native UTM optical grids cannot be used in the production area path. Use 10 m EPSG:6933 for hectare sensitivity.
- The existing pipeline already supports mean(NDVI), full months, counts and absolute change; proposed additions are configurable relative-domain diagnostics, common-support export and per-pixel acquisition-membership evidence. No production monthly-method changes were implemented.
- Generic pipeline reporting has CDN links; the separate draft builder vendors cached local Leaflet and avoids local JSON fetch.
- Reconciler and reviewed-evidence release adapter remain planned/unimplemented; the private planning adapter cannot satisfy those executed graph nodes.
- Proposed hosts/separate sessions and per-step resource budgets need confirmation. Selecting Codex/Claude does not prove a native delegated subagent.
- private-bundles exists locally with .git; remote identity/privacy/ownership was not verified and it was not modified. No public-bundles repository was created.
- Draft redistribution licenses, full Leaflet license and privacy review remain release blockers. A private draft is not a publication license.

## Implemented and proposed tree

```text
forest_change/bundle.py                   implemented private draft builder/verification
scripts/build_bundle.py                   thin local CLI
tests/test_bundle.py                     six packaging integrity tests
tests/check_bundle_browser.cjs           explicit local Chromium smoke check
docs/portable_bundle.md                  builder contract and limitations
docs/architecture_audit.md               append-only structural review
reviews/road-like-ndvi-2025-2026-monthly/
  starter/{README.md,docs/*.md}           preserved starter document inputs
  rounds/round-0001/                     supplied proposal unchanged + canonical renders
  rounds/round-0002/
    round.yaml; graph.{mmd,svg}; assignments/; roles/
    inputs/                             AOI, original ROIs, exact windows and locations
    bootstrap/                          observed provenance, integrity checks and logs
    curated/                            explicit local packaging inputs; PNGs ignored
    planning_changes.md; monthly_pair_proposal.md; data_license_estimate.md
    planning_tables/; bundle_spec.json; handoff.md; index.html
    artifacts/<role>/                    PROPOSED, not created as executed evidence
  private-drafts/build-0003/bundles/forest-road-ndvi-aoi-example-2025-2026/round-0002/
    index.html; report.{html,md}; bundle_manifest.json
    metadata/{claim_matrix,disagreements,sources}.csv; harness.json; round.yaml
    metadata/{assignments,roles,standing_roles,inputs}/; graph.{mmd,svg}
    figures/archived-{reference,target}.png
    maps/{index.html,leaflet.js,leaflet.css,images/}
    agents/<id>/{index.html,plan.md,report.md,execution.json}
    inquiry/round-0002.md; planning_changes.md; monthly_pair_proposal.md; data_license_estimate.md
  .../round-0002.zip                     local private archive, not published
```

See monthly_pair_addendum.md: item counts are not automatically unique-acquisition counts; reject/group duplicate overpasses explicitly, and record the unimplemented mask-dilation sensitivity. The private bundle proposal snapshot predates this final local code-review addendum; approval must use this complete local packet.

## Checks and next approval

Schema/graph validator and pinned renderer --check pass for both planned rounds. Assignment hashes, standing-role hashes, original overlay bytes and copied ROI/control bytes are checked separately. No structural pass is scientific verification. Private final draft and ZIP-extracted copy both verify 74 files and 45 local HTML/CSS links. A real Chromium file:// test of the extracted copy blocked all external requests, switched both historical PNGs, displayed four ROI/control features and recorded zero page errors/requests. The frozen metadata/round.yaml also passes Lab validation after ZIP extraction. Unit tests and synthetic demo outputs are captured in bootstrap/checks/; those synthetic data are not field evidence.

Next human decision: approve the round-0002 graph and its seven-step sequence, provisionally select these archived ROI/control polygons and the June windows, and authorize ONLY audit-01 from authenticated local caches, with an explicit bound of at most 80 tool calls / 30 minutes and no remote data access. Discovery, scientific quantification, data-access freeze, branch acceptance, challenge acceptance, release and promotion remain separately gated. This question records no approval; all YAML approvals stay pending.

Disturbance candidates are not legal deforestation, confirmed forest state or causal loss labels. Hansen annual loss is not monthly ground truth. Sensor agreement does not establish cause.
