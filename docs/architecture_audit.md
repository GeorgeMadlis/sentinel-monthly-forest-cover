# Architecture audit log

Entries record structural/contract review; they do not establish scientific accuracy.

## 2026-10-21 — Agent harness and explicit Lab validation

**Trigger:** Added repository instructions, round integration guide, explicit Lab validator
adapter, offline adapter tests and CI. Baseline Sentinel commit:
`24c6e98adf225e3de9cf4184a404aa27b4ff8104`.
Lab harness commit: `ab8f5af440ced93e2e577635b825a5880fa48e98`.

**Drift review:** Applied Forest Cover Lab's governance/drift_checklist.md against this
downstream change. Mission remains forest-cover disturbance evidence. Lab owns P1 search
protocol and sources, P2 dataset suitability, P3 external-code discovery and P4 scientific
reverse engineering; this patch changes none of those contracts or inventories. P5 local
processing, research, corroboration and reporting responsibilities remain independently
enterable, with round records supplementing existing shared ledgers. P6 authority boundaries
are documented; reusable roles/schema stay upstream while operational evidence stays here.
Forest definitions, equal-area hectares, nodata, monthly weak-supervision non-claims,
GEE independence and human promotion gates are retained. Scientific corpus and existing
skills, runs, review evidence and candidate findings are unchanged.

**Actual validation:**

- Baseline `.venv/bin/python -m unittest discover -v`: 39 tests, four errors. All four
  concerned stale Lab graph pins (descriptor/provenance/semantic trace), before harness edits.
- Final same command: 42 tests in 15.498 s, OK, no skips. Includes synthetic pipeline,
  manifest/provenance, descriptor, semantic-path, review-site and three adapter tests.
  Deliberate invalid-link test output is expected and its rejection test passes.
- `.venv/bin/python ../forest-cover-lab/graph/build.py --check --descriptor workflow.yaml`:
  PASS; 68 concepts, 72 validated and 67 candidate relationships; graph revision
  `3e6dc320bd9f59a483d605d100614005eaa1beb35139edcd1d7d37f04914380a`.
- `.venv/bin/python scripts/validate_agent_rounds.py --lab ../forest-cover-lab`:
  PASS, zero manifests (none recorded; no claim of validation of historical investigations).
- `.venv/bin/python -m compileall -q scripts/validate_agent_rounds.py
  tests/test_agent_harness.py` and `git diff --check`: PASS.
- Local Python assertions verified CI's Lab checkout pin equals workflow.yaml's full Lab
  commit, its graph revision equals the local graph, and standing host documentation has
  no removed client names: PASS. Lab separately passes 104 tests, including synthetic
  completed records, downstream round paths and invalid provenance rejection.

**Reconciliation:** These checkouts had no AGENTS.md or CLAUDE.md; both were added rather
than overwriting prior instructions. Standing documentation contained no named unused
client to remove. All four Codex skills and portable review contracts remain unchanged;
their availability is not treated as invocation. No real round was created or historical
execution backfilled. The adapter requires --lab explicitly; Lab tests do not traverse a
sibling checkout. New CI checks out the exact Lab commit and validates Sentinel rounds
locally. The package's schema remains upstream rather than being copied and forked here.

**Existing compatibility repair:** Only knowledge_snapshot's two pins changed in
workflow.yaml. The old Lab revision `f3895e46fe3a5109e8bf0e3e01328e942b1e98c5` and graph
`ef90b703ae150c09cc7cac6fd324d7b5ecd8305a5a0d5130ec0deb61ed291e49` were replaced by the
above reviewed local Lab commit/current graph. Registered methods, implementation version,
divergences, scientific definitions and descriptor declaration status were preserved.
Historical run manifests were not repinned. Passing checks validate compatibility, not
scientific equivalence or empirical accuracy.

**Unresolved / review status:** ADR 0006 and policy await operator review. Hosted CI has
not run; its Lab commit is local until publication is authorized, so remote checkout cannot
succeed before that object becomes available. The CLI checks declarations, not actual
model loads, evidence authenticity, independence or append-only history. Existing scientific
and implementation gaps (including temporal persistence, external SAR preprocessing and
independent accuracy labels) remain unchanged. No notification, scheduler or automatic
orchestration/promotion is implemented. No merge, push or scientific approval is asserted.

**Reviewer:** Codex structural/contract review; human review pending.

**Changed-file inventory:** AGENTS.md; CLAUDE.md; README.md; docs/architecture.md;
docs/agent_harness.md; docs/architecture_audit.md; scripts/validate_agent_rounds.py;
tests/test_agent_harness.py; workflow.yaml; .github/workflows/contracts.yml.


## 2026-10-21 — Publication reconciliation and final Lab pin

**Trigger:** Operator authorized commit, push and merge. Fetching current main revealed
`30f2e08` had added standing instructions and a re-pin to Lab `71f5481`. Merged that history
into the feature branch and resolved instruction/descriptor conflicts. Kept all upstream
processing, nodata, equal-area, provenance, demo, re-pin and convention constraints; added
round responsibilities rather than replacing those constraints. Current standing host text
names ChatGPT, Claude, Claude Code and Codex. Historical validation/audit entries are retained.

**Compatibility review:** Lab's reconciled harness commit is
`85281485ac82d4a40a4b1e05e25c8102c9178bdb`. Reviewed its changes since the upstream descriptor
pin: governance/instructions, harness contracts/tests and generated overview changed;
knowledge, graph inputs, scientific inventories and consumed DS-0002/DS-0003 meanings did
not. Graph revision remains `3e6dc320bd9f59a483d605d100614005eaa1beb35139edcd1d7d37f04914380a`.
CI and workflow.yaml both pin this exact commit, retaining all declarations/divergences.

**Actual checks:** `.venv/bin/python -m unittest discover -v`: 42 tests, OK, 14.594 s.
`.venv/bin/python ../forest-cover-lab/graph/build.py --check --descriptor workflow.yaml`:
PASS. `.venv/bin/python scripts/validate_agent_rounds.py --lab ../forest-cover-lab`:
PASS, zero recorded rounds. Ran the documented synthetic demo with
`scripts/create_synthetic_fixture.py --directory /private/tmp/sentinel-harness-merged-demo`
and `scripts/run_pipeline.py --manifest /private/tmp/sentinel-harness-merged-demo/workflow.yaml
--forest-def /private/tmp/sentinel-harness-merged-demo/forest.yaml
--aoi-geojson /private/tmp/sentinel-harness-merged-demo/aoi.geojson`: PASS. Lab
validate_provenance accepted its manifest; local assertions confirmed CI/descriptor pin
alignment. Synthetic outputs remain temporary test fixtures, not scientific findings.
`git diff --check`: PASS. Hosted CI follows publication and is reported in the PR.

**Drift review / open findings:** Mission and P1–P6 retained; no new research track,
scientific source, independent validation result, existing run/review mutation or knowledge
promotion. Lab's newly fetched diagram governance is preserved upstream and its overview
regenerated through the generator. The initial missing-overview/local-only limitations
are superseded by this publication work. Existing scientific/host-authenticity limitations
remain. Authorization to merge infrastructure is separate from scientific review; proposed
ADR status is not changed by this record. Reviewer: Codex integration/contract checks.


## 2026-10-22 — Lab candidate agent-governance graph compatibility review

User authorized integration of agent-harness recommendations and a fresh Lab KG viewer.
Lab HEAD is `d67e08354d748f1bd9423af1953de31244671f53` (dirty integration tree), Sentinel HEAD is
`bacbea70cf3badb1c137285f827b3570f84c0c22`. Lab graph revision is `359109d4c2801c71b6cb37026cd0a9b7a1c42a6db5a085f880ecd6919a133062`. Its 20 new concepts and
37 relationships are candidates; 72 prior validated relationships are unchanged. ADRs
0006/0007 and scientific promotion retain their human-review gates. Operational runs,
review bundles and production descriptor pins were not rewritten. This entry records
integration checks, not an executed scientific investigation or a backfilled round.

Reviewed Lab governance/drift_checklist.md: forest-cover mission, semantic/executable/run
boundaries, source/tool separation and independent tracks are preserved. Lab README,
overview, glossary, role registry and audit were updated together. Existing P2 in-situ
inventory gap and the explicitly disclosed earlier unscoped source consultation remain
limitations. No orchestration engine, independent source confirmation, scientific
threshold or forest/legal claim was added.

Actual checks: Lab `.venv/bin/python -m pytest --tb=short` passed 132 tests; Lab graph,
illustrative descriptor, planned-round validator and generated overview checks passed.
The updated offline Chromium viewer interaction check passed. From this checkout,
`.venv/bin/python scripts/validate_agent_rounds.py --lab /Users/server/projects/forest-cover-lab`
passed with zero manifests recorded. `.venv/bin/python -m unittest discover -v` ran
42 tests: 38 passed and four reported graph/provenance revision errors. The descriptor
check also reports a stale graph. Baseline comparison confirmed this pin mismatch already
existed before the edits (Lab baseline `950e1405aacb2d6459745d7f2e0674890249752ebc952b58ad34bbc7e8e5e146`
versus this workflow's `3e6dc320bd9f59a483d605d100614005eaa1beb35139edcd1d7d37f04914380a`).
The synthetic demo under `/tmp/lab-agent-kg-demo.xT1WlV` passed using the documented fixture
and pipeline commands. Full commands and viewer checksums are in the appended Lab audit.

Follow-up adoption requires a reviewed/committed Lab snapshot, upstream-diff review and
both full commit/graph pins, then the descriptor check, unit tests and synthetic demo.
Do not use an old commit to claim this dirty graph is committed. Reviewer: Codex structural
review only; human/operator review pending. No check promotes scientific candidates.


## 2026-10-22 — Publication and committed Lab snapshot adoption

User explicitly authorized commit, push and merge. Lab PR #8 merged as
`c322e89fb96def2434c62776ac595f6cd995ef92` after both hosted CI runs passed. Main had gained round-agent graphs
under ADR 0007, so the candidate KG discovery proposal was renumbered to ADR 0008;
the prior audit entry above retains the earlier local proposal name and graph revision.
The reconciled Lab suite passed 172 tests and retained original graph approvals, loop
bounds, planning images and 1.0 schema behavior alongside 1.1 provenance capture.

Reviewed the entire Lab diff since `85281485ac82d4a40a4b1e05e25c8102c9178bdb`,
especially knowledge/, graph/ and the DS-0002/DS-0003 rows. Scientific concepts and
existing relationships are unchanged; the workflow record adds a candidate harness link.
Workflow descriptor and CI now pin the merged Lab commit and graph `f70789df04b79ca8ec65e0094c571e0b3f6844afa2b88af2f8c9bcf1776a20f7`.
No scientific processing or divergences changed. The harness guide distinguishes the
reusable KG, optional round plan/approvals and runtime evidence.

Actual post-pin checks from this checkout:

- `.venv/bin/python -m unittest discover -v`: **42 passed**, 0 errors (14.820 s).
- `.venv/bin/python ../forest-cover-lab/graph/build.py --check --descriptor workflow.yaml`:
  **PASS**, 88 concepts, 72 validated and 104 candidate relationships.
- `.venv/bin/python scripts/validate_agent_rounds.py --lab /Users/server/projects/forest-cover-lab`:
  **PASS**, zero operational manifests recorded.
- `.venv/bin/python scripts/create_synthetic_fixture.py --directory /var/folders/_y/yj6hdhbs057c4bnyg_ff8xt80000gn/T/sentinel-kg-repin-demo-4m3bdhba` followed by
  `.venv/bin/python scripts/run_pipeline.py --manifest /var/folders/_y/yj6hdhbs057c4bnyg_ff8xt80000gn/T/sentinel-kg-repin-demo-4m3bdhba/workflow.yaml --forest-def /var/folders/_y/yj6hdhbs057c4bnyg_ff8xt80000gn/T/sentinel-kg-repin-demo-4m3bdhba/forest.yaml --aoi-geojson /var/folders/_y/yj6hdhbs057c4bnyg_ff8xt80000gn/T/sentinel-kg-repin-demo-4m3bdhba/aoi.geojson`:
  **PASS**. Lab validate_provenance accepted the synthetic output manifest and committed
  graph. This uses no EO downloads, credentials or model inference.

Lab drift checklist review: mission and P1–P6 boundaries preserved; the optional round
graph/image freshness requirement is retained. Existing P1/P2 source-process and in-situ
inventory limitations stay documented upstream. Historical run/review files were not
changed. This re-pin resolves the prior four downstream test errors; it does not
validate scientific candidates or accept proposed ADRs. Reviewer: Codex integration
and compatibility checks; human scientific review remains pending.

The final offline viewer was exported from a clean clone of merged Lab main into
`forest-cover-lab/outputs/kg-viewer-f70789df04b7/`; metadata records c322e89,
`dirty: false`, and a fresh graph. Local Chromium graph/deep-link/role navigation and
catalogue filters passed with zero page errors and external page requests blocked.
Viewer manifest SHA-256: `09c2121e759e9e82302ed430023ce5526bc95efd4d4756ca30f83dbd9b2b1633`.

## 2026-10-23 — Local road-investigation planning bootstrap and private draft builder

**Trigger:** The operator authorized local planning against a starter ZIP and a separate
portable private-draft implementation, with explicit graph/step/data/release gates.
No remote discovery/download, scientific-role execution, publication, merge or promotion
was authorized. Attached starter documents were treated as inputs subordinate to the
request and Lab contracts.

**Baselines:** Sentinel `2f512fec185d1290ab5203c8892231f2d5c219be`; Lab
`c322e89fb96def2434c62776ac595f6cd995ef92`; graph
`f70789df04b79ca8ec65e0094c571e0b3f6844afa2b88af2f8c9bcf1776a20f7`.
All match the starter; no re-pin or Lab edit was needed. Sentinel was initially clean.
Lab's modified pyproject.toml and five untracked files remain untouched; exact initial
status is in the new round's bootstrap/provenance.json. These HEADs identify the baseline,
not the newly written, uncommitted builder. Freeze a new baseline before later execution.

**Review against Lab governance/drift_checklist.md:** Mission boundary retained: Lab owns
science/governance, Sentinel owns implementation and local review artifacts. P1: source
provenance, SHA-256 and explicit not-run/pending status retained; no scientific search or
inventory insertion occurred. P2: provider/scene/date/license statements remain archived
context or unverified planning assumptions; no source listing was promoted to evidence.
P3/P4: code assessment remains a local implementation-gap proposal; no external source
inventory or Lab method was changed. P5: the private draft builder is separate from
scientific processing and from the unimplemented reviewed-evidence release adapter.
P6: both planned rounds validate and both canonical graph renders are current. The Lab
checklist's upstream inventory/track/overview items are not modified or independently
re-audited by this downstream change; no full Lab governance audit is claimed.

**Changes:** Nine starter overlay files were copied only into an absent investigation
path and remain byte-identical. Round-0001 is preserved; round-0002 documents revised
artifact handoffs, hashed primary-evidence access for challenge/assembly, removal of a
future-bundle dependency, cache-only pre-freeze audit and equal-area sensitivity bounds.
The original four ROI/control polygons are copied byte-for-byte, with overlay QA pending.
All approvals are pending, all selections planned and all actual_executions arrays empty.
No logical role is represented as an observed native delegated subagent.

`forest_change/bundle.py` and its thin CLI stage a curated private planning draft in a
new directory, verify input/assignment/output hashes, copy original assignment and
round-only-role paths for extracted round validation, include source PNGs/local Leaflet,
and emit an adjacent ZIP. Failed builds are discarded from temporary staging; overwrite
is refused. Manifest inventory excludes only itself. This adapter accepts planned drafts
only and cannot execute or publish the graph's future reviewed-evidence assembly node.
Source PNG snapshots/private drafts are ignored by Git. The public release gate remains
pending; local private-bundles existence does not verify its remote/privacy or authorize use.

**Actual verification:** 48 unit tests passed (14.824 s), including six new packaging
integrity tests. The documented local synthetic fixture and pipeline demo passed. The
Lab descriptor check passed: 88 concepts, 72 validated and 104 candidate relationships.
The explicit-Lab round validator passed for two schema-1.1 records, including carried
artifacts and branch independence constraints; pinned renderer --check passed for both.
Additional checks authenticated all seven plan hashes, selected-role hashes, unchanged
starter overlay bytes, original ROI/control bytes and six historical evidence-file hashes.
The private final draft and its ZIP-extracted copy verified 74 files and 45 HTML/CSS local
dependencies. Extracted metadata/round.yaml passed Lab validation. The whole new local
investigation index checked 160 relative HTML/CSS dependencies without a broken target.
Real Chromium opened the ZIP-extracted file:// entry/report/map with external requests
blocked: two archived PNG layers switched, four ROI/control features rendered, zero page
errors and zero attempted external requests. Initial sandbox browser launch failed on macOS
Mach-port permission; the same local test passed after approved sandbox escalation.
These are packaging/synthetic/structural checks, not scientific verification or approval.

**Open findings / human status:** ROI identity and overlay QA, 13 historical manifest/hash
mismatches, the 2025-layer/2023-flight contradiction, forest baseline/labels, clear-scene
availability, provider data/license/transfer estimates, full Leaflet redistribution license,
proposed host availability and per-step budgets remain unresolved. Monthly relative/support
diagnostics, unique-acquisition counting and mask-dilation sensitivity are proposed only; reconciler and reviewed-evidence release adapter are not
implemented. Every release/promotion decision still requires human review.

**Reviewer:** Codex local structural review; human review pending. No scientific candidate
was accepted or promoted. Exact validation argv, timestamps, logs and provenance are under
reviews/road-like-ndvi-2025-2026-monthly/rounds/round-0002/bootstrap/.


## 2026-10-24 — Authorized audit-01 local-cache execution

**Authorization and scope:** User explicitly approved the round-0002 graph and audit-01 only, bounded to 80 tool calls / 30 minutes with no remote access. The two outlined corridors were confirmed as intended targets; orthophoto before/after-July-2025 and Hansen 2024/free-service directions were captured for later gated work. The assignment and graph topology/digests were preserved; approval/status/attempt records and canonical status renders were updated. No other role, download, paid external service, release, merge or knowledge promotion occurred.

**Observed execution:** Sequential logical role in the current Codex session; no native delegated subagent. Client/serving-model details and private external instructions remain uncaptured. Both repository HEADs and the Lab graph remain at the prior pins, with unrelated local edits preserved. Main scientific audit scripts read only authenticated local files. Elapsed time including preflight was 1013.1 seconds at closure, below 1800 seconds; manually tracked calls remain below 80. Hosted session billing is not observable, so free external-service use is not asserted as free model billing.

**Drift review:** Mission boundary and P1/P2 evidence/lineage/non-claims retained; no external inventories or scientific definitions were changed (P3/P4 not expanded). Audit evidence is downstream and portable (P5). Both old review/run evidence and prior audit-log prefix remain unchanged; graph/step approvals precede the sole recorded attempt, current graph render and schema validation pass (P6). Future changed harness/temporal-baseline assumptions need a successor plan, rather than editing this executed assignment.

**Actual checks/results:** 79 source assets authenticated against original manifests; calibrated optical 59/59 and sigma/radar 213/226 output hashes match. All 301 historical-original and 910 historical-artifact hashes match, and all 1514 original run/review files are unchanged. The same 13 historical mismatches are retained and excluded from original-manifest authority; four production masks reproduce exactly and 11 continuous raster/count comparisons pass 2e-6 tolerance. Four unchanged valid ROI/control polygons lie inside the AOI; two optical landmark tests prefer zero integer shift. Historical manifests validate against their own graphs retrieved from local Git objects, and the new audit reproduction manifest passes current run schema/semantic validation. The portable audit site passes strict checks: 69 HTML pages, zero link problems. No real browser test was performed in this audit; local image tools inspected raw/outline/control and all four existing-rule mask variants.

**Open findings:** Surveyed road edges, subpixel/full-corridor/SAR registration, independent control stability, orthophoto flight-to-pixel dates, a Lab-compatible 2024 forest temporal interpretation and local Hansen asset availability remain limited/unresolved. Hansen v1.12 treecover2000 is year-2000 cover despite the product edition. Generic acquisition grouping and dilation, reconciler and reviewed release adapter remain future gated work. Only audit outputs are completed; human scientific/output acceptance and every subsequent gate remain pending.

**Evidence/reviewer:** Codex bounded source/code/geometry/reproduction audit. Evidence, actual source dates/URLs, commands, script hashes, run manifest and output hashes are under reviews/road-like-ndvi-2025-2026-monthly/rounds/round-0002/artifacts/audit-01/ and its schema-1.1 attempt in round.yaml. This is reproducibility/structural evidence, not empirical scientific verification.


## 2026-10-24 — Authorized source and audit-record publication

**Trigger:** User explicitly requested commit, push and merge after audit completion. Scope is the Sentinel implementation, planned/operational round records, audit evidence and documentation; unrelated dirty Lab files remain untouched. Private draft bundles, source PNG staging and derived raster caches remain ignored/local. No later scientific gate or curated bundle release is approved by this source-control operation.

**Checks before commit:** 48 unit tests passed in 14.590 s; Lab descriptor/graph freshness, both local round validators, canonical round renderer --check and git diff --check passed. Remote Sentinel main equals local baseline 2f512fec185d1290ab5203c8892231f2d5c219be. Publication review found no credential/signature patterns in the intended source/review text. Full Leaflet 1.9.4 BSD license was retrieved from its tagged upstream LICENSE via GitHub connector (blob bcb3ba1aca095155857556d96e3193a50fe1bd11) and added with a notice under third_party/leaflet/. Historical audit files/manifests are preserved; their prior license/pin observations are not rewritten.

**Drift review:** Mission and Lab authority unchanged; P1/P2 source/evidence separation and non-claims preserved, P3/P4 no research inventory expansion, P5 private planning adapter remains separate from scientific execution/release, P6 both round graphs current and schema checks pass. This publication carries the recorded audit limitations and pending human output/scientific review; no automatic promotion. Hosted CI and merge outcome are reported through the pull request, not anticipated here.

**Staged-byte review:** The first cached whitespace check exposed intentional CRLF in the vendored Leaflet CSS and two CSV snapshots, previously untracked during the working-tree check. Added three narrow .gitattributes rules to preserve those hashed bytes and recognize CR-at-EOL; no evidence was normalized. Cached whitespace validation then passed.


## 2026-10-24 — Round-0003: synthesis-01 sub-agent and retasked geo-01/works-01

**Trigger:** Operator asked to add a sub-agent that scans, analyses and summarises the existing sub-agents' results, retasks them if needed with online public sources, and writes an offline HTML report (ASD-STE100 style) on ROI-01/ROI-02: 2025 existence, artificial widening, and use of Maa- ja Ruumiamet / Transpordiamet information.

**Structure:** New successor round reviews/road-like-ndvi-2025-2026-monthly/rounds/round-0003/ with a round-only role (roles/evidence-synthesis.md), assignment synthesis-01.md, retask addenda for geo-01 (0001) and works-01 (0001, 0002), byte-identical copies of round-0002 inputs and base assignments, artifacts for all three instances and a canonical graph render. Round-0002 is unchanged: its approved graph places geo-01/works-01 behind a pending freeze gate that requires discovery-01, so new attempts could not be recorded there. geo-01/works-01 outputs were first written under round-0002/artifacts/ and moved unchanged (artifacts/RELOCATION.md). No standing Lab role or registry was edited.

**Observed execution:** synthesis-01 ran sequentially in Claude Code and spawned geo-01 and works-01 as native background subagents (Claude Code, model reported as claude-opus-5-5); works-01 was resumed once (retask 0002). Lab AGENTS.md and docs/agents.md were loaded after start (recorded as limitations). The round-graph approval is a retrospective record of the operator instruction; no graph image was shown before execution. Human review is pending.

**Drift review:** Mission boundary and non-claims retained in the report (P1/P2). No forest definition, threshold or dataset role introduced; the NDVI contrast width setting is labelled report configuration (P3/P4). Evidence stays downstream with hashes; raw downloads and full-size images git-ignored; copyrighted news HTML kept local only (P5). Validators pass; no promotion (P6). New finding: ROI length_m and the 40 m buffer were computed in EPSG:6933 (ground lengths 18.3 km and 8.6 km); distances and widths should use EPSG:3301.

**Checks:** scripts/validate_agent_rounds.py PASS for rounds 0001–0003 (structure only); Lab render_round_graph.py --check PASS (3 graphs); 48 unit tests OK; report bundle 38 files, all local links resolve, headless Chromium renders at 1100 px and 390 px. Reviewer: synthesis-01 structural review; human review pending.
