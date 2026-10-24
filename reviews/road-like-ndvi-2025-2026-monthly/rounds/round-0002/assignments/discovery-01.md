# discovery-01 — Dataset/tool discovery and verification

**Round:** round-0002 (planned). **Host (proposed):** `chatgpt`. **Role:** `agent_harness/roles/dataset-and-tool-discovery.md` (`standing`).

## Question
Find viable dated Sentinel scenes, aerial orthophotos, ETAK roads and official road/rail geometry with license/availability. Do not treat source listing as acquired evidence.

## Inputs and authority
Inputs: AOI, preliminary ROI IDs, month windows, provider/source preferences, no assumed independent ground truth.
Lab and Sentinel scientific/provenance policy has priority over this assignment. Data access is read-only outside new round output directories. No agent promotes knowledge or publishes a public release.

## Bounded step plan
1. Verify Earth Search or STAC Sentinel-2 L2A and radar products for both full Junes, and image access/cost.
2. Verify official Estonian historical orthophoto/WMS layer names, flight dates, GSD, terms; flag previously contradictory 2023/2025 metadata.
3. Verify ETAK historical/current road representations and Transpordiamet Teeregister or official Rail Baltic alignments.
4. Find forest-cover baseline if a forest-specific claim is sought; state forest definition and license as pending until approved.
5. Rank FAIR-inspired criteria, spatial/temporal coverage, quality and lineage. Keep automatic catalogue leads unverified.

## Output contract
Write `dataset_options.csv` into this round's artifacts directory or a new read-only-referenced run directory. For each claim include `claim_id`, `roi_id`, `period`, `status`, `evidence_ids`, `source_lineage`, `limitations`. Record tools, original observations, acquisition/registration dates, hashes, data/license terms and negative findings. An unavailable input produces a clearly marked blocker, not invented output.

## Acceptance / stop rules
PASS if every selected link has access evidence, dates/scale limitations, producer and lineage. BLOCK if selected datasets cannot be legally accessed or dated.

## Review
Step plan and outputs require human approval at the declared graph gates. `actual_executions` is empty until a host actually performs the task. No unreviewed source is ground truth.

## Successor planning constraints
Predecessor: round-0001, retained unchanged. This is a logical role plan, not proof of native delegation. Proposed hosts require availability checks; separate sessions need manual handoff. Null budgets are unspecified and require a bounded approval. Record actual model/runtime, prompt, loaded file SHA-256 values, exact commands, timestamps, source URLs/dates and limitations under schema 1.1 only after approval. No actual attempts are recorded in this bootstrap.
