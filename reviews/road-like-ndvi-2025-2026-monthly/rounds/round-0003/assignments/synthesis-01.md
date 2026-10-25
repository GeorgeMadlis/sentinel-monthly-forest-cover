# synthesis-01 — Cross-instance evidence synthesis and offline report

**Round:** round-0002 (added 2026-10-24 by operator request). **Host:** `claude-code`. **Role:** `roles/evidence-synthesis.md` (`round_only`).

## Question
For ROI-01 and ROI-02: (1) Did the outlined roads exist in 2025? (2) If they existed in 2025, are there signs of artificial widening? (3) Use Maa- ja Ruumiamet (Maa-amet), Transpordiamet (Teeamet) or similar official sources where they help answer (1) and (2).

## Inputs and authority
Recorded outputs of audit-01 and of any retasked instance, the 2026-10-06 review, round inputs and Lab contracts. Public, free online sources (operator-authorized 2026-10-24). No credentials, paid services or bulk scene downloads. Lab and Sentinel scientific/provenance policy has priority.

## Bounded step plan
1. Inventory the executed outputs and their hashes. Record which instances did not run.
2. Identify evidence gaps for questions 1–3. Retask geo-01 and works-01 with written addenda when gaps exist.
3. Analyse the returned evidence against the competing hypotheses in round.yaml.
4. Write report/index.html in ASD-STE100 style (about 80 % conformance), with sources, links, images and an evidence table per ROI.
5. Make the report folder self-contained (local images, relative links, no CDN) and write a manifest with SHA-256 values.

## Output contract
`synthesis_report/index.html`, `synthesis_report/assets/`, `synthesis_claims.csv`, `synthesis_sources.csv`, `synthesis_manifest.json`. Claim columns: `claim_id`, `roi_id`, `question`, `status`, `evidence_ids`, `source_lineage`, `limitations`.

## Acceptance / stop rules
PASS if every answer cites dated evidence and states its status and limitations. Return indeterminate where dated evidence is missing. Human review remains pending; this step does not open the decision gate.

Disturbance candidates are not legal deforestation, confirmed forest state or causal loss labels. Sensor agreement does not establish cause.
