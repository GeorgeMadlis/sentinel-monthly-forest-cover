# Observed development checks and limits

Initial packaging unit checks exposed a missing bundle_manifest.json navigation target before manifest creation; the builder now creates the target before link auditing and excludes it from its own inventory. Builds now stage into a temporary sibling and expose a completed result only after verification. Corrected six packaging tests passed, followed by the full 48-test suite (final captured run: 14.824 s).

The first Chromium launch within the managed sandbox failed with macOS Mach-port bootstrap permission. The same installed local browser test passed after tool approval of sandbox escalation, with external requests blocked. No auto-review rejection occurred. Browser module/client paths were supplied explicitly; no package/browser was downloaded.

Private build-0001 (in the original private-drafts/bundles path), build-0002 and build-0003 are preserved as separate local drafts. Build-0002 adds frozen assignment/role/input snapshots and geometry-only AOI digest. Build-0003 updates the archived source CSV; original per-scene dates are retained, while historical retrieval timestamps remain not_captured_in_bootstrap. The selected final private draft is build-0003. Earlier local drafts were not overwritten or published.

A temporary audit-placement assertion initially tested the wrong suffix condition; inspection confirmed the historical audit was already preserved as the exact prefix. The final audit entry is appended after that original prefix. This did not change any historical review evidence.

Planning bootstrap/runtime observations belong in bootstrap/provenance.json and check logs, not in a fabricated specialist actual_executions attempt. Precise serving model settings, Codex client version and private external instructions remain uncaptured. No delegated scientific-role runtime is claimed.
