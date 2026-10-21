# Agent harness integration

ChatGPT, Claude, Claude Code and Codex identify hosts/clients. A specialist is a logical
responsibility, not a vendor process or scientific authority. Read [AGENTS.md](../AGENTS.md)
and the selected Lab checkout's docs/agents.md and proposed ADR 0006 for reusable roles,
schema, templates and planning examples. Lab remains scientific/governance authority.

For actual investigations create reviews/<investigation-id>/rounds/<round-id>/round.yaml
with assignments/ and optional task configs, source scopes and scripts. Assignments resolve
relative to that round; standing roles resolve relative to the explicitly selected Lab.
Additional local role files require `role_scope: round_only`. A new round never requires
editing the standing Lab registry. Record actual execution progressively, including both
full commit pins and dirty state in the evidence ledger, Lab graph revision, host, loaded
rule/role/assignment/skill hashes, source lineage, exact commands, outputs and checksums.
Executed loaded files must match their declared pinned revision; changed instructions
need a new round rather than silently changing the baseline pin. Completed attempts map
every output reference to its SHA-256 in `output_hashes`. Uncaptured private external
instructions require an explicit limitation; never copy private content or credentials.

Round records supplement run manifests, investigation.json, semantic_trace.json, findings
and evidence ledgers. They do not replace them. Keep existing review paths, portable HTML
and candidate staging rules. Old reviews without rounds remain historical evidence; do
not infer hosts or backfill executions. Generated assignments cannot override scientific
contracts. No orchestration, automatic delegation or promotion is implemented here.

The four standing tool skills remain unchanged:

- [.codex/skills/inspect-sentinel-change/SKILL.md](../.codex/skills/inspect-sentinel-change/SKILL.md)
- [.codex/skills/research-sentinel-change/SKILL.md](../.codex/skills/research-sentinel-change/SKILL.md)
- [.codex/skills/corroborate-sentinel-change/SKILL.md](../.codex/skills/corroborate-sentinel-change/SKILL.md)
- [.codex/skills/report-sentinel-change/SKILL.md](../.codex/skills/report-sentinel-change/SKILL.md)

Each has its own agents/openai.yaml runtime metadata and references/investigation-contract.md;
inspect additionally has references/threshold-protocol.md and scripts/robust_threshold.py.
These are instructions/configuration, not scientific source observations. Record them
when actually loaded; availability does not prove use. Other hosts need explicit content.

Run from this repository with its environment and an explicit Lab checkout:

```sh
.venv/bin/python -m unittest discover -v
.venv/bin/python scripts/validate_agent_rounds.py --lab /path/to/forest-cover-lab
.venv/bin/python /path/to/forest-cover-lab/graph/build.py --check --descriptor workflow.yaml
```

CI checks out Lab at the full commit pinned in its workflow, installs this repository's
requirements, runs its tests and these two validators. The round check discovers local
reviews only (plus any locally added examples/inquiries); it never relies on Lab's tests
traversing a sibling checkout. Zero rounds means none recorded, not a validation of older
investigations. The CLI is read-only. Structural validation checks declarations, not file
digest authenticity, actual host use, append-only history or scientific correctness.

Human review remains pending for this architecture and every candidate scientific result.
