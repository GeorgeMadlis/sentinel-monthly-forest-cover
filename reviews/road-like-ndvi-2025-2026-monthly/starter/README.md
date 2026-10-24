# Road-like NDVI monthly investigation — starter package

**Status: PLANNED; no satellite analysis, agent execution or public release performed.** Built against Forest Cover Lab `c322e89fb96def2434c62776ac595f6cd995ef92` and Sentinel `2f512fec185d1290ab5203c8892231f2d5c219be` on 2026-10-23.

**Open [`preview/index.html`](preview/index.html) on your computer** to inspect the dependency graph and all seven agent plans without an internet connection. The standalone [`preview/graph.svg`](preview/graph.svg) is a preview; the canonical renderer should generate `round-0001/graph.svg` and `graph.mmd` after copying to local Sentinel checkout.

Package paths:

- `sentinel-overlay/reviews/road-like-ndvi-2025-2026-monthly/rounds/round-0001/round.yaml`: schema 1.1 planned graph (human gates pending).
- `.../assignments/*.md`: seven independently inspectable per-agent step plans with hash references in graph.
- `.../roles/pipeline-audit.md`: one task-only role; six existing Lab standing roles are reused.
- `docs/SCIENTIFIC_PROTOCOL.md`: monthly comparison, formula, confounder and QA requirements.
- `docs/BUNDLE_ARCHITECTURE.md`: result archives, offline HTML, provenance, round trajectory, public/private safety.
- `handoff/CODEX_CLAUDE_CODE_PROMPT.md`: the single execution bootstrap for local repo implementation.
- `handoff/CHAT_PROJECT_SYNC.md`: common project instruction extension for ChatGPT and Claude.
- `preview`: interactive-inspectable *static* offline plan; NOT measured results.

Use the canonical hand-off prompt with Codex **or** Claude Code, not two simultaneous unsynchronized edits. Review the graph and plan first, then authorize actual data downloads and tests. Public repository creation is intentionally deferred to a human release decision. `private-bundles` and `public-bundles` could not be confirmed through the current linked GitHub connector; a missing repository is not proof it does not exist under another owner/connection.

See the official Lab graph reference in `agent_harness/examples/road-widening/round-0001/round.yaml`, which is an unexecuted example with some overlapping concerns. This starter adds monthly aggregation, road/rail dating, true optical controls, and multi-host synchronization.
