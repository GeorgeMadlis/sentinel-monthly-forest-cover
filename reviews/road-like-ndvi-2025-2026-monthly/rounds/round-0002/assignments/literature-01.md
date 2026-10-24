# literature-01 — Mechanism and methods literature

**Round:** round-0002 (planned). **Host (proposed):** `chatgpt`. **Role:** `agent_harness/roles/literature-and-media.md` (`standing`).

## Question
Assess mechanisms for month-year NDVI artifacts, mixed road edges, phenology, radar disagreements, structural road change and independent tests.

## Inputs and authority
Inputs: question, methods, confounders, dates; no need to see later EO judgment.
Lab and Sentinel scientific/provenance policy has priority over this assignment. Data access is read-only outside new round output directories. No agent promotes knowledge or publishes a public release.

## Bounded step plan
1. Search journals/technical papers for interannual single-month NDVI differences and edge-sensitive linear-feature artifacts.
2. Search specifically for cloudy observation distributions, phenology, vegetation regrowth, mixed pixels, BRDF, correction/registration effects, road verges, agriculture and radar-surface interactions.
3. Extract exact applicability conditions for change detection, minimum observations, trend/baseline comparisons, uncertainty and thresholds.
4. Separate a general mechanism supported in literature from local observed causality.
5. Provide DOI/links, search queries/date, duplicated source lineage and falsifiable expectations for both ROIs.

## Output contract
Write `literature_ledger.csv, literature_claims.csv` into this round's artifacts directory or a new read-only-referenced run directory. For each claim include `claim_id`, `roi_id`, `period`, `status`, `evidence_ids`, `source_lineage`, `limitations`. Record tools, original observations, acquisition/registration dates, hashes, data/license terms and negative findings. An unavailable input produces a clearly marked blocker, not invented output.

## Acceptance / stop rules
PASS if alternate mechanisms and discriminating tests are traceable, and no general mechanism is presented as site evidence.

## Review
Step plan and outputs require human approval at the declared graph gates. `actual_executions` is empty until a host actually performs the task. No unreviewed source is ground truth.

## Successor planning constraints
Predecessor: round-0001, retained unchanged. This is a logical role plan, not proof of native delegation. Proposed hosts require availability checks; separate sessions need manual handoff. Null budgets are unspecified and require a bounded approval. Record actual model/runtime, prompt, loaded file SHA-256 values, exact commands, timestamps, source URLs/dates and limitations under schema 1.1 only after approval. No actual attempts are recorded in this bootstrap.

Also produce literature_primary_evidence.json: a machine-readable list of source and derived artifact paths, SHA-256 values, acquisition/publication/retrieval dates, license, lineage and missing-input status. The reconciler must preserve these references for challenge and assembly. Shared providers do not establish independent source lineage.
