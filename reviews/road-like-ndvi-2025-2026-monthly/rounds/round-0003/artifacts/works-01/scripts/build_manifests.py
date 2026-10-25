"""Build works_primary_evidence.json and execution.json with SHA-256 of all files. Usage: python -I build_manifests.py WORKS_DIR ENDED_UTC"""
import json, sys, hashlib, os, csv, datetime
d, ended = sys.argv[1], sys.argv[2]
def sha(p):
    h = hashlib.sha256(); h.update(open(p, 'rb').read()); return h.hexdigest()
def mtime(p): return datetime.datetime.fromtimestamp(os.path.getmtime(p), datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
ledger = list(csv.DictReader(open(f'{d}/works_ledger.csv', encoding='utf8')))
files = []
for root, _, fs in os.walk(d):
    for f in sorted(fs):
        p = os.path.join(root, f); rel = os.path.relpath(p, d)
        if rel in ('works_primary_evidence.json', 'execution.json'): continue
        kind = 'source_download' if rel.startswith('downloads/') else 'derived' if rel.startswith(('derived_', 'images/')) else 'script' if rel.startswith('scripts/') else 'report'
        ev = [r['evidence_id'] for r in ledger if any(rel.endswith(x.strip().split('/')[-1]) and x.strip().split('/')[-1] for x in r['local_path'].split(';'))]
        files.append({'path': rel, 'kind': kind, 'sha256': sha(p), 'bytes': os.path.getsize(p), 'written_or_retrieved_utc': mtime(p), 'evidence_ids': ev})
ev = {'schema': 'works-01 primary evidence v1', 'round': 'round-0002', 'instance': 'works-01', 'retask': 'works-01-retask-0001',
      'roi_input': {'path': 'inputs/prior_rois.geojson', 'sha256': 'b079d3dbff8a473daf6e3d33cdfdaedffc29de470425b8fe9a212f796a862125'},
      'sources': [{k: r[k] for k in ('evidence_id', 'source_type', 'publisher', 'title_or_layer', 'url', 'document_or_data_date', 'event_date', 'retrieval_utc', 'local_path', 'license_terms', 'geometry_match_confidence')} for r in ledger],
      'files': files,
      'lineage_notes': ['E01-E08, E11: Maa- ja Ruumiamet registers via gsavalik.envir.ee (shared provider; ETAK, cadastre, planning are distinct registers but one provider).',
                        'E09-E10: Keskkonnaagentuur Metsaregister via the same WFS host (shared provider, distinct register).',
                        'E12-E17: ERR news, single secondary lineage; not independent confirmations of each other.',
                        'E20: derived by works-01 scripts from E01-E11.'],
      'missing_inputs': [{'item': 'Rail Baltica Tootsi-Pärnu design alignment / building permit / works log', 'status': 'not_found', 'refs': ['N02', 'N04']},
                         {'item': 'Are bypass (road 4 km 108.5-115.8) design geometry / building permit', 'status': 'not_found', 'refs': ['N03', 'N04']},
                         {'item': 'Procurement register IDs (riigihanked.riik.ee)', 'status': 'blocked', 'refs': ['N01']},
                         {'item': 'Actual felling/earthwork dates', 'status': 'not_available_in_official_sources_found'},
                         {'item': 'Control polygon coverage', 'status': 'not_assessed (outside download bboxes)'}]}
json.dump(ev, open(f'{d}/works_primary_evidence.json', 'w', encoding='utf8'), indent=1, ensure_ascii=False)
L = '/Users/server/projects/forest-cover-lab'; S = '/Users/server/projects/sentinel-monthly-forest-cover'; R = f'{S}/reviews/road-like-ndvi-2025-2026-monthly/rounds/round-0002'
ex = {'instance': 'works-01', 'role': 'official-infrastructure-records', 'round': 'round-0002',
      'host': 'claude-code (subagent spawned by synthesis-01)', 'model': 'claude-opus-5-5 (as reported by runtime)',
      'started_utc': '2026-10-24T16:37:40Z', 'ended_utc': ended,
      'repositories': {'sentinel-monthly-forest-cover': '5b2e30e11d2ea9a990878f4bee643c11864daae3 (HEAD at run; working tree had untracked round-0002 files)',
                       'forest-cover-lab': 'c322e89fb96def2434c62776ac595f6cd995ef92', 'graph_revision': 'f70789df04b79ca8ec65e0094c571e0b3f6844afa2b88af2f8c9bcf1776a20f7'},
      'loaded_harness': [
          {'path': f'{S}/AGENTS.md', 'sha256': sha(f'{S}/AGENTS.md'), 'when': 'before start (delivered via project instructions CLAUDE.md -> AGENTS.md in the session context)'},
          {'path': f'{S}/CLAUDE.md', 'sha256': sha(f'{S}/CLAUDE.md'), 'when': 'before start (session context)'},
          {'path': '/Users/server/projects/CLAUDE.md', 'sha256': sha('/Users/server/projects/CLAUDE.md'), 'when': 'before start (session context)'},
          {'path': f'{L}/agent_harness/roles/official-infrastructure-records.md', 'sha256': sha(f'{L}/agent_harness/roles/official-infrastructure-records.md'), 'when': 'read at start 2026-10-24T16:37:40Z'},
          {'path': f'{R}/assignments/works-01.md', 'sha256': sha(f'{R}/assignments/works-01.md'), 'when': 'read at start'},
          {'path': f'{R}/assignments/works-01-retask-0001.md', 'sha256': sha(f'{R}/assignments/works-01-retask-0001.md'), 'when': 'read at start'},
          {'path': f'{R}/inputs/prior_rois.geojson', 'sha256': sha(f'{R}/inputs/prior_rois.geojson'), 'when': 'read at start (data input)'},
          {'path': f'{L}/AGENTS.md', 'sha256': sha(f'{L}/AGENTS.md'), 'when': 'read AFTER start, at 2026-10-24T16:39:18Z, on coordinator harness update (after ETAK/RB WFS downloads had begun)'},
          {'path': f'{L}/docs/agents.md', 'sha256': sha(f'{L}/docs/agents.md'), 'when': 'read AFTER start, at 2026-10-24T16:39:18Z (first ~250 lines displayed; file hashed in full)'}],
      'not_read': ['docs/agent_harness.md (sentinel) referenced by CLAUDE.md was not opened', 'reviews/20261006T174722Z-sentinel-road-investigation/* and artifacts/audit-01/* (deliberately not read)'],
      'private_external_instructions': 'coordinator prompt from synthesis-01: not_captured verbatim (summarised: scope, write-only directory, authorized public sources, independence rules, outputs, budget)',
      'tools': ['Bash (curl WFS GetCapabilities/GetFeature to gsavalik.envir.ee; curl of web pages; shasum; pdftotext)', 'python3 -I and sentinel .venv python -I (shapely, pyproj, matplotlib)', 'WebSearch (7 queries)', 'WebFetch (5 calls; 2 failed: 404/DNS)', 'Read (2 PNG previews)', 'ToolSearch (1)'],
      'commands_summary': ['WFS GetFeature bbox 534600,6476200,547700,6489700 and 529400,6485600,531800,6494300 (EPSG:3301) for etak e_501/e_502/e_503/e_601/e_603',
                           'WFS planeeringud:rb_planeeringutrass; kitsendus_suunatud kpo/kma transport+planeering; planeeringud yld/detail plan layers; metsaregister teatis + teatis_arhiiv (RD,LR); kataster ky_kehtiv (CQL by tunnus, by address LIKE raudtee/Ikla tee, by registr>=2019); ehak asustusyksuste_piirid',
                           'scripts/intersect_etak.py, intersect_polygon_layer.py, profile_centreline.py, vertex_distances.py, intersect_forest_notices.py, parcel_coverage.py, parcels_in_roi.py, notice_chainage.py, archive_notices.py, roi_villages.py, render_map.py, build_manifests.py'],
      'tool_call_count_estimate': 72, 'budget': '120 tool calls / 60 min; used ~72 calls / ~16 min',
      'outputs': {f: sha(f'{d}/{f}') for f in ('works_ledger.csv', 'works_claims.csv', 'README.md', 'works_primary_evidence.json')},
      'checks': ['CSV column-count consistency checked (ledger 14 cols, claims 10 cols)', 'Map PNGs visually inspected', 'No files written outside artifacts/works-01/'],
      'limitations': ['Web searches are non-replayable; results summarised by the search tool may contain errors (one summary mis-stated a contract year; corrected from saved ERR page metadata).',
                      'ERR articles are a single secondary lineage; lead-partner conflict E12 vs E13 unresolved.',
                      'No official design geometry for RB Tootsi-Pärnu or Are bypass; identity of ROI-01 SW part and ROI-02 N part indeterminate.',
                      'Forest-notice approval dates are not felling dates.', 'Controls not assessed.', 'riigihanked.riik.ee not machine-accessible; no procurement IDs.']}
json.dump(ex, open(f'{d}/execution.json', 'w', encoding='utf8'), indent=1, ensure_ascii=False)
print('files', len(files))
