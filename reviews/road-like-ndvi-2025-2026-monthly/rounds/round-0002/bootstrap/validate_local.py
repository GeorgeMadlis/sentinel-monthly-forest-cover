"""Capture actual local checks. This is bootstrap validation, not a graph runner."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import tempfile

here = Path(__file__).resolve().parent
root = here.parents[4]
lab = root.parent / 'forest-cover-lab'
python = str(root / '.venv/bin/python')
checks = here / 'checks'
checks.mkdir(exist_ok=True)
rounds = root / 'reviews/road-like-ndvi-2025-2026-monthly/rounds'
bundle = root / 'reviews/road-like-ndvi-2025-2026-monthly/private-drafts/build-0002/bundles/forest-road-ndvi-aoi-example-2025-2026/round-0002'


def run(name, args):
    start = datetime.now(timezone.utc).isoformat()
    p = subprocess.run(args, cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    end = datetime.now(timezone.utc).isoformat()
    (checks / (name + '.log')).write_text(p.stdout)
    return {'name': name, 'argv': args, 'cwd': str(root), 'started_utc': start,
            'ended_utc': end, 'exit_code': p.returncode, 'output': name + '.log',
            'scope': 'local synthetic/structural/packaging check, not scientific verification'}


commands = [
    ('unit_tests', [python, '-m', 'unittest', 'discover', '-v']),
    ('round_schema_graph', [python, str(root / 'scripts/validate_agent_rounds.py'), '--lab', str(lab)]),
    ('graph_freshness', [python, str(lab / 'agent_harness/scripts/render_round_graph.py'),
                         str(rounds / 'round-0001/round.yaml'), str(rounds / 'round-0002/round.yaml'), '--lab', str(lab), '--check']),
    ('descriptor', [python, str(lab / 'graph/build.py'), '--check', '--descriptor', str(root / 'workflow.yaml')]),
    ('planning_integrity', [python, str(here / 'check_plan.py'), str(lab)]),
    ('bundle_inventory', [python, str(root / 'scripts/build_bundle.py'), '--verify', str(bundle)]),
    ('whitespace', ['git', 'diff', '--check']),
]
with ThreadPoolExecutor(max_workers=4) as pool:
    results = list(pool.map(lambda c: run(*c), commands))
# The fixture must exist before the pipeline can consume it. Both are local only.
fixture = Path(tempfile.mkdtemp(prefix='forest-road-synthetic-'))
results.append(run('synthetic_fixture', [python, str(root / 'scripts/create_synthetic_fixture.py'), '--directory', str(fixture)]))
if results[-1]['exit_code'] == 0:
    results.append(run('synthetic_pipeline', [python, str(root / 'scripts/run_pipeline.py'),
        '--manifest', str(fixture / 'workflow.yaml'), '--forest-def', str(fixture / 'forest.yaml'),
        '--aoi-geojson', str(fixture / 'aoi.geojson')]))
(checks / 'commands.json').write_text(json.dumps(results, indent=2) + '\n')
for r in results:
    print(r['name'], 'PASS' if r['exit_code'] == 0 else 'FAIL', flush=True)
raise SystemExit(any(r['exit_code'] for r in results))
