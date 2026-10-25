# Relocation note (synthesis-01, 2026-10-24)

geo-01 and works-01 ran with output directories under
`rounds/round-0002/artifacts/{geo-01,works-01}/`, as named in their retask briefs.
The round-0002 graph was already approved and could not record new attempts for them
(its freeze gate is pending and requires discovery-01). The attempts are therefore recorded in
successor round-0003. synthesis-01 moved both directories unchanged (`mv`, no content edit) to
`rounds/round-0003/artifacts/`. Absolute paths inside their execution.json,
geo_primary_evidence.json and works_primary_evidence.json still name round-0002. Read
`round-0002/artifacts/<id>/` as `round-0003/artifacts/<id>/`. File hashes are not affected.

Retask briefs that the agents read from `round-0002/assignments/` are byte-identical to the copies in
`round-0003/assignments/` (same SHA-256). Round-0002 is restored to its committed state.

Git: geo-01 `raw/` and `images/` (59 MB) and works-01 `downloads/` (17 MB, includes copyrighted ERR
HTML kept only for hashing) are git-ignored. Hashes remain in the agents' evidence files. The offline
report bundle holds compressed copies of the figures it uses.
