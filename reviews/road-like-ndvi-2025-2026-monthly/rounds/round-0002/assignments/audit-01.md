# audit-01 — Pipeline/code and prior-evidence audit

**Round:** round-0002 (planned). **Host (proposed):** `codex`. **Role:** `roles/pipeline-audit.md` (`round_only`).

## Question
Check previous outputs, exact NDVI formulas, imagery dates, calibration, geo-registration and reference ROI coordinates. Keep 2026-10-06 evidence unchanged.

## Inputs and authority
Inputs: pinned AOI, original 2026-10-06 review (report.md, rois.geojson, report.html, raster_audit.json), current single-scene and summer configs.
Lab and Sentinel scientific/provenance policy has priority over this assignment. Data access is read-only outside new round output directories. No agent promotes knowledge or publishes a public release.

## Bounded step plan
1. Verify previous report/ROI IDs, no silent changes, and exact available source-window hashes.
2. Find both corridor centreline/buffers and controls in prior rois.geojson; verify geometries within AOI and explain which portion represents two road-like features.
3. Trace map legend and code to determine whether existing display is absolute NDVI difference or relative percentage, including denominator and handling near zero.
4. Recreate existing signal only from authenticated local cached scene windows and compare checksums where possible. No new downloads before the data-access freeze gate; missing or mismatched historical inputs are blockers.
5. Inspect spatial registration, SCL nodata, reflectance offset flags, scene counts, resampling and prior WMS acquisition-date conflict.
6. Export roi_review.geojson by copying verified geometries (with original source checksum), preserving controls; mark if a manual ROI approval is needed.

## Output contract
Write `audit_report.md, roi_review.geojson` into this round's artifacts directory or a new read-only-referenced run directory. For each claim include `claim_id`, `roi_id`, `period`, `status`, `evidence_ids`, `source_lineage`, `limitations`. Record tools, original observations, acquisition/registration dates, hashes, data/license terms and negative findings. An unavailable input produces a clearly marked blocker, not invented output.

## Acceptance / stop rules
PASS if road sampling geometries are explicitly pinned, old run unchanged, all QA limits stated. BLOCK if ROI identity, old source hashes or formula semantics cannot be checked.

## Review
Step plan and outputs require human approval at the declared graph gates. `actual_executions` is empty until a host actually performs the task. No unreviewed source is ground truth.

## Successor planning constraints
Predecessor: round-0001, retained unchanged. This is a logical role plan, not proof of native delegation. Proposed hosts require availability checks; separate sessions need manual handoff. Null budgets are unspecified and require a bounded approval. Record actual model/runtime, prompt, loaded file SHA-256 values, exact commands, timestamps, source URLs/dates and limitations under schema 1.1 only after approval. No actual attempts are recorded in this bootstrap.

Do not reconstruct new centrelines from buffered polygon vertices. The archive contains two corridor polygons and two visual controls; source centreline recovery and overlay QA remain pending. Also write audit_evidence_manifest.json with original source paths, hashes and QA status.
