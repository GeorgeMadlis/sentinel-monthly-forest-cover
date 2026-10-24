# challenge-01 — Independent falsification and alternative hypotheses

**Round:** round-0002 (planned). **Host (proposed):** `claude`. **Role:** `agent_harness/roles/independent-challenge.md` (`standing`).

## Question
Inspect primary rasters and records and challenge time attribution, prior-road presence, classifier thresholds, forest definition, apparent source independence and conclusions.

## Inputs and authority
Inputs: independent branch artifacts, source data & hash ledgers, reconciled claims, prior 2026-10-06 review, approval history.
Lab and Sentinel scientific/provenance policy has priority over this assignment. Data access is read-only outside new round output directories. No agent promotes knowledge or publishes a public release.

## Bounded step plan
1. Recompute a sample of key pixel values and common-support area independently; confirm raw observations rather than report summaries.
2. Challenge the claim that road presence proves no corridor modifications or vegetative disturbance.
3. Test whether changing month, valid-scene counts, road buffers and optical calibration reverses the interpretation.
4. Revisit 2025 orthophoto dating conflict and road vs railway alternative; check source-lineage independence.
5. Audit pre-assembly figures, map manifest and proposed narrative for omission of disagreement, missing forest mask, unsupported causes or absent negative evidence.
6. Return claim-by-claim supported/contradicted/indeterminate and concrete next-round tasks.

## Output contract
Write `challenge_report.md, challenge_claims.csv` into this round's artifacts directory or a new read-only-referenced run directory. For each claim include `claim_id`, `roi_id`, `period`, `status`, `evidence_ids`, `source_lineage`, `limitations`. Record tools, original observations, acquisition/registration dates, hashes, data/license terms and negative findings. An unavailable input produces a clearly marked blocker, not invented output.

## Acceptance / stop rules
PASS if counterexamples, unresolved gaps and reproduced checks are recorded even when conclusions remain inconclusive.

## Review
Step plan and outputs require human approval at the declared graph gates. `actual_executions` is empty until a host actually performs the task. No unreviewed source is ground truth.

## Successor planning constraints
Predecessor: round-0001, retained unchanged. This is a logical role plan, not proof of native delegation. Proposed hosts require availability checks; separate sessions need manual handoff. Null budgets are unspecified and require a bounded approval. Record actual model/runtime, prompt, loaded file SHA-256 values, exact commands, timestamps, source URLs/dates and limitations under schema 1.1 only after approval. No actual attempts are recorded in this bootstrap.

Consume primary_evidence_index.json, resolve original rasters/records by hash, and report inaccessible sources. The final assembled bundle is checked by the human release gate after assembly; do not require a future artifact before this role can start. Reconciled conclusions have been received, so report conclusion_exposure: received; this role is a challenge, not a blinded independent observation.
