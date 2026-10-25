# geo-01 — Historical national geospatial corroboration

**Round:** round-0002 (planned). **Host (proposed):** `claude-code`. **Role:** `agent_harness/roles/national-geospatial-evidence.md` (`standing`).

## Question
Inspect pinned ROI geometries against dated authoritative orthophotos, ETAK mapping and metadata; do not use EO conclusions to guide interpretation.

## Inputs and authority
Inputs: ROI geometries and windows only; avoid reading EO conclusions until independent observations archived.
Lab and Sentinel scientific/provenance policy has priority over this assignment. Data access is read-only outside new round output directories. No agent promotes knowledge or publishes a public release.

## Bounded step plan
1. Retrieve official ETAK current/historical road geometries near both ROI traces and controls.
2. Select actual year-specific orthophotos (earlier than 2025 and 2025/2026 if available), verify provider metadata by map sheet, not only WMS layer labels.
3. Distinguish acquisition date, mosaic edition, WMS request time and interpretation date. Record pixel GSD and positional accuracy where published.
4. Classify centreline/track/road/rail presence at each dated source: present, absent with usable coverage, indeterminate, or unavailable. Avoid inferring absence from missing imagery.
5. Export a dated screenshot/georeferenced window where license permits, plus per-source hashes and a source-derived map overlay.

## Output contract
Write `geo_sources.csv, geo_claims.csv` into this round's artifacts directory or a new read-only-referenced run directory. For each claim include `claim_id`, `roi_id`, `period`, `status`, `evidence_ids`, `source_lineage`, `limitations`. Record tools, original observations, acquisition/registration dates, hashes, data/license terms and negative findings. An unavailable input produces a clearly marked blocker, not invented output.

## Acceptance / stop rules
PASS if year-to-year assertions cite genuinely dated imagery at feature scale. BLOCK if 2025 layer vs 2023 flight-date conflict remains unresolved; still report indeterminate.

## Review
Step plan and outputs require human approval at the declared graph gates. `actual_executions` is empty until a host actually performs the task. No unreviewed source is ground truth.

## Successor planning constraints
Predecessor: round-0001, retained unchanged. This is a logical role plan, not proof of native delegation. Proposed hosts require availability checks; separate sessions need manual handoff. Null budgets are unspecified and require a bounded approval. Record actual model/runtime, prompt, loaded file SHA-256 values, exact commands, timestamps, source URLs/dates and limitations under schema 1.1 only after approval. No actual attempts are recorded in this bootstrap.

Also produce geo_primary_evidence.json: a machine-readable list of source and derived artifact paths, SHA-256 values, acquisition/publication/retrieval dates, license, lineage and missing-input status. The reconciler must preserve these references for challenge and assembly. Shared providers do not establish independent source lineage.
