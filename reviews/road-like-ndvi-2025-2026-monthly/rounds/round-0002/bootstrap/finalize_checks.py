"""Check the selected private draft after ZIP extraction; capture observed results."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

here = Path(__file__).resolve().parent
root = here.parents[4]
sys.path.insert(0, str(root))
from forest_change.bundle import audit_links, verify_bundle

parser = argparse.ArgumentParser()
parser.add_argument('--puppeteer-module', required=True)
parser.add_argument('--browser', required=True)
args = parser.parse_args()
checks = here / 'checks'
lab = root.parent / 'forest-cover-lab'
bundle = root / 'reviews/road-like-ndvi-2025-2026-monthly/private-drafts/build-0003/bundles/forest-road-ndvi-aoi-example-2025-2026/round-0002'
archive = bundle.with_suffix('.zip')
extracted = Path(tempfile.mkdtemp(prefix='forest-road-final-extracted-'))
with zipfile.ZipFile(archive) as z:
    z.extractall(extracted)
result = {'directory': verify_bundle(bundle), 'zip_extracted': verify_bundle(extracted)}
commands = []


def run(name, argv):
    started = datetime.now(timezone.utc).isoformat()
    p = subprocess.run(argv, cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    entry = {'name': name, 'argv': argv, 'cwd': str(root), 'started_utc': started,
             'ended_utc': datetime.now(timezone.utc).isoformat(), 'exit_code': p.returncode,
             'output': name + '.log'}
    commands.append(entry)
    (checks / entry['output']).write_text(p.stdout)
    if p.returncode:
        raise RuntimeError(p.stdout)
    return p.stdout


try:
    run('extracted_round', [sys.executable, str(lab / 'agent_harness/scripts/validate_round.py'),
        str(extracted / 'metadata/round.yaml'), '--lab', str(lab)])
    browser_result = run('browser_final', ['node', str(root / 'tests/check_bundle_browser.cjs'),
        args.puppeteer_module, args.browser, str(extracted), '/tmp/forest-road-private-draft-final-map.png'])
    result['browser'] = json.loads(browser_result)
    run('planning_final', [sys.executable, str(here / 'check_plan.py'), str(lab)])
    run('graphs_final', [sys.executable, str(lab / 'agent_harness/scripts/render_round_graph.py'),
        '--root', str(root), '--lab', str(lab), '--check'])
    run('whitespace_final', ['git', 'diff', '--check'])
    run('historical_tracked_unchanged', ['git', 'diff', '--exit-code', 'HEAD', '--',
        'reviews/20261006T174722Z-sentinel-road-investigation'])
    old_audit = subprocess.check_output(['git', 'show', 'HEAD:docs/architecture_audit.md'], cwd=root)
    assert (root / 'docs/architecture_audit.md').read_bytes().startswith(old_audit)
    result['historical_audit_prefix_unchanged'] = True
    result['all_investigation_html_css_links'] = audit_links(bundle.parents[4])
    result['bundle_manifest_sha256'] = hashlib.sha256((bundle / 'bundle_manifest.json').read_bytes()).hexdigest()
    result['zip_sha256'] = hashlib.sha256(archive.read_bytes()).hexdigest()
    result['scientific_verification'] = False
    (checks / 'final_results.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
finally:
    (checks / 'final_commands.json').write_text(json.dumps(commands, indent=2) + '\n')
