# works-01 — Official road/rail construction records

**Round:** round-0002 (planned). **Host (proposed):** `claude`. **Role:** `agent_harness/roles/official-infrastructure-records.md` (`standing`).

## Question
Test identity and construction/maintenance intervals for ROI-01/02 with spatially matched official records; never infer Rail Baltica just from proximity.

## Inputs and authority
Inputs: geographic candidate ROI geometry and dates, without EO interpretations.
Lab and Sentinel scientific/provenance policy has priority over this assignment. Data access is read-only outside new round output directories. No agent promotes knowledge or publishes a public release.

## Bounded step plan
1. Identify candidate infrastructure lines and maintenance projects by official geometry intersection, not name/proximity alone.
2. Check construction/permit/contract/map documents for road or rail at the site and timestamp.
3. Separate road existed, expanded, maintained, vegetation cleared, rail project works, and uncertain project linkage.
4. Log source URLs, project IDs, document dates, event dates and map geometry confidence.
5. Provide positive and negative search results in original Estonian terms where relevant.

## Output contract
Write `works_ledger.csv, works_claims.csv` into this round's artifacts directory or a new read-only-referenced run directory. For each claim include `claim_id`, `roi_id`, `period`, `status`, `evidence_ids`, `source_lineage`, `limitations`. Record tools, original observations, acquisition/registration dates, hashes, data/license terms and negative findings. An unavailable input produces a clearly marked blocker, not invented output.

## Acceptance / stop rules
PASS if claim-to-geometry and claim-to-event dates are traceable; otherwise return indeterminate, not construction confirmed.

## Review
Step plan and outputs require human approval at the declared graph gates. `actual_executions` is empty until a host actually performs the task. No unreviewed source is ground truth.

## Successor planning constraints
Predecessor: round-0001, retained unchanged. This is a logical role plan, not proof of native delegation. Proposed hosts require availability checks; separate sessions need manual handoff. Null budgets are unspecified and require a bounded approval. Record actual model/runtime, prompt, loaded file SHA-256 values, exact commands, timestamps, source URLs/dates and limitations under schema 1.1 only after approval. No actual attempts are recorded in this bootstrap.

Also produce works_primary_evidence.json: a machine-readable list of source and derived artifact paths, SHA-256 values, acquisition/publication/retrieval dates, license, lineage and missing-input status. The reconciler must preserve these references for challenge and assembly. Shared providers do not establish independent source lineage.
