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
