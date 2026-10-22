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
