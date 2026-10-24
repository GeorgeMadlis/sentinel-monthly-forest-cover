# Private offline planning drafts

`scripts/build_bundle.py` packages a curated round-local `bundle_spec.json` into a
**new** destination and adjacent ZIP. It reads only local inputs, verifies their hashes,
and refuses overwrite. Processing and verification live in `forest_change/bundle.py`.
The present adapter deliberately supports `private_planned_draft` only: it cannot
package executed evidence as an approved release or publish anything.

```sh
.venv/bin/python scripts/build_bundle.py --review reviews/road-like-ndvi-2025-2026-monthly/rounds/round-0002 --destination /tmp/forest-road-private-draft
.venv/bin/python scripts/build_bundle.py --verify /tmp/forest-road-private-draft
```

Open `index.html` directly with `file://`. Plans, reports, GeoJSON, PNGs, Leaflet and
its vendor images are local. The map uses embedded JSON and local image URLs; it
does not fetch local JSON or use a tile service. A gray background or transparent
image pixel is unavailable context. Planned monthly layers are explicitly absent.

The spec lists local curated files with `path`, `destination`, `sha256`, source/date,
lineage and license metadata; `map_layers` lists PNGs and archived WGS84 bounds.
`metadata` carries forest-mask/label/license status and upstream worktree limits.
The builder checks HTML/CSS relative links and writes a manifest listing every
included file except the manifest itself, its byte size and SHA-256. After extracting
the ZIP, run `--verify` again. Browser testing must block external network requests.
The manifest is an inventory; authenticity of evidence and scientific review need
their own records. It does not sign itself or certify redistribution rights.

The release layout follows the supplied `BUNDLE_ARCHITECTURE.md`: report HTML and
Markdown, metadata tables, frozen round, figures, offline maps, per-role plans/reports/
explicit not-run execution records, and inquiry decisions. A planned draft retains
pending gates rather than inventing an approved frozen graph. A future release adapter
must consume completed records and human approval of all curated content, dates,
licenses, privacy and map semantics. No such approval is inferred here.

Disturbance candidates are not legal deforestation, confirmed forest state or causal
loss labels. Hansen annual loss is not monthly ground truth. Sensor agreement does
not establish cause.
