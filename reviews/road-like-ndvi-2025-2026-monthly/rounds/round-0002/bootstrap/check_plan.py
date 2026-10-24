"""Local planning checks only; do not create specialist execution records."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

import yaml

round_dir = Path(__file__).resolve().parents[1]
root = round_dir.parents[3]
lab = Path(sys.argv[1]).resolve()
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
record = yaml.safe_load((round_dir / 'round.yaml').read_text())
provenance = json.loads((round_dir / 'bootstrap/provenance.json').read_text())
for repo, key in [(root, 'sentinel_monthly_forest_cover'), (lab, 'forest_cover_lab')]:
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip() == record['repos'][key]
assert json.loads((lab / 'graph/generated/knowledge.json').read_text())['revision'] == record['repos']['lab_graph_revision']
assert record['schema_version'] == '1.1' and record['status'] == 'planned'
assert record['graph']['mode'] == 'stepwise'
assert record['graph']['approval']['status'] == record['human_review']['status'] == 'pending'
hashes = {}
for instance in record['instances']:
    assert instance['actual_executions'] == []
    assert instance['selection_status'] == 'planned'
    role_root = round_dir if instance['role_scope'] == 'round_only' else lab
    assert (role_root / instance['role']).is_file()
    assignment = round_dir / instance['assignment']
    node = next(n for n in record['graph']['nodes'] if n.get('instance') == instance['id'])
    hashes[instance['id']] = sha(assignment)
    assert node['step_plan']['plan_sha256'] == hashes[instance['id']]
    assert node['step_plan']['approval']['status'] == 'pending'
    for ref in instance['harness_sources']:
        assert ref['capture_status'] == 'selected'
        ref_root = round_dir if ref['source'] == 'round' else lab
        assert sha(ref_root / ref['path_or_identifier']) == ref['sha256']
for node in record['graph']['nodes']:
    if node['kind'] == 'gate':
        assert node['approval']['status'] == 'pending'
for path, before in provenance['history_before'].items():
    assert sha(root / path) == before
history = root / 'reviews/20261006T174722Z-sentinel-road-investigation/rois.geojson'
assert (round_dir / 'inputs/prior_rois.geojson').read_bytes() == history.read_bytes()
assert len(json.loads(history.read_text())['features']) == 4
archive = Path('/Users/server/projects/uploaded_artifacts/forest-cover-lab/forest-road-investigation-starter.zip')
assert sha(archive) == provenance['starter_zip_sha256']
count = 0
with zipfile.ZipFile(archive) as z:
    prefix = 'forest-road-investigation-starter/sentinel-overlay/'
    for name in z.namelist():
        if name.startswith(prefix) and not name.endswith('/'):
            assert (root / name.removeprefix(prefix)).read_bytes() == z.read(name)
            count += 1
for ref in provenance['loaded_local_planning_files']:
    repo = root if ref['repository'] == root.name else lab
    assert sha(repo / ref['path']) == ref['sha256']
    blob = subprocess.check_output(['git', 'show', ref['revision'] + ':' + ref['path']], cwd=repo)
    assert hashlib.sha256(blob).hexdigest() == ref['sha256']
print(json.dumps({'result': 'PASS', 'scope': 'planning integrity, not science',
    'imported_files_unchanged': count, 'roi_control_features_unchanged': 4,
    'plan_sha256': hashes, 'actual_executions_total': 0, 'all_approvals': 'pending'}, indent=2))
