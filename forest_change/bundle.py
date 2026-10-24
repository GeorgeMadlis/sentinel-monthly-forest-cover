"""Build a new, private, offline planning draft from explicitly curated local files.

This module never discovers imagery, downloads dependencies, executes a role, or
releases a bundle. Its manifest describes copied bytes, not scientific validation.
"""
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path, PurePosixPath
import shutil
import tempfile
from urllib.parse import unquote, urlsplit
import zipfile

import yaml


NON_CLAIMS = ('Disturbance candidates are not legal deforestation, confirmed forest state '
              'or causal loss labels. Hansen annual loss is not monthly ground truth. '
              'Sensor agreement does not establish cause.')


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def local_file(root, reference):
    """Only ordinary files within an explicitly chosen root, including no symlinks."""
    rel = PurePosixPath(reference)
    if rel.is_absolute() or not rel.parts or any(p in ('.', '..') for p in rel.parts):
        raise ValueError(f'Unsafe relative file: {reference}')
    root = Path(root).resolve()
    target = root.joinpath(*rel.parts)
    if not target.resolve().is_relative_to(root) or any(p.is_symlink() for p in (target, *target.parents) if p != root):
        raise ValueError(f'Unsafe file: {reference}')
    if not target.is_file():
        raise ValueError(f'Missing file: {reference}')
    return target


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def page(title, body):
    return ('<!doctype html><html lang="en"><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<meta http-equiv="Content-Security-Policy" content="default-src \'self\' data:; '
            'script-src \'self\' \'unsafe-inline\'; style-src \'self\' \'unsafe-inline\'; '
            'img-src \'self\' data:; connect-src \'none\'">'
            f'<title>{html.escape(title)}</title><style>body{{font:16px system-ui;max-width:1100px;'
            'margin:2em auto;padding:0 1em;line-height:1.5}}pre{white-space:pre-wrap;overflow-wrap:anywhere}'
            'img{max-width:100%}table{border-collapse:collapse}td,th{border:1px solid #aaa;padding:.5em}'
            '</style><body>' + body + '</body></html>')


class References(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        self.links.extend(v for k, v in attrs if k in ('href', 'src') and v)


def audit_links(root):
    """Check HTML/CSS local dependencies without fetching anything."""
    import re
    root = Path(root).resolve()
    checked = 0
    for path in sorted(root.rglob('*')):
        if path.suffix not in ('.html', '.css'):
            continue
        content = path.read_text(encoding='utf-8')
        if path.suffix == '.html':
            parser = References()
            parser.feed(content)
            refs = parser.links
        else:
            refs = [v.strip(' \'\"') for v in re.findall(r'url\(([^)]+)\)', content)]
        for ref in refs:
            if ref.startswith(('data:', '#')):
                continue
            uri = urlsplit(ref)
            if uri.scheme or uri.netloc or uri.path.startswith('/'):
                raise ValueError(f'Nonportable dependency in {path.name}: {ref}')
            target = (path.parent / unquote(uri.path)).resolve()
            if not target.is_relative_to(root) or not target.is_file():
                raise ValueError(f'Broken local dependency in {path.name}: {ref}')
            checked += 1
    return checked


def verify_bundle(root):
    root = Path(root)
    manifest = json.loads((root / 'bundle_manifest.json').read_text())
    entries = manifest['files']
    if len({e['path'] for e in entries}) != len(entries):
        raise ValueError('Duplicate manifest entries')
    expected = {e['path'] for e in entries}
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    if actual != expected | {'bundle_manifest.json'}:
        raise ValueError('Manifest file inventory differs from bundle')
    for entry in entries:
        p = local_file(root, entry['path'])
        if p.stat().st_size != entry['size_bytes'] or digest(p) != entry['sha256']:
            raise ValueError(f'Checksum mismatch: {entry["path"]}')
    return {'files_verified': len(entries), 'local_links_checked': audit_links(root),
            'scientific_verification': False}


def _build_draft(review, destination):
    """Copy a curated spec into a new draft directory and adjacent ZIP; refuse overwrite."""
    review, destination = Path(review).resolve(), Path(destination).resolve()
    spec = json.loads((review / 'bundle_spec.json').read_text())
    archive = destination.with_suffix('.zip')
    if destination.exists() or archive.exists():
        raise ValueError('Choose a new destination; existing bundles are immutable')
    if destination.is_relative_to(review):
        raise ValueError('Bundle output must be separate from the review inputs')
    if spec['status'] != 'private_planned_draft':
        raise ValueError('Only private planned drafts are implemented; release needs human review')
    round_file = local_file(review, 'round.yaml')
    record = yaml.safe_load(round_file.read_text())
    if record['status'] != 'planned' or any(i['actual_executions'] for i in record['instances']):
        raise ValueError('This draft adapter accepts planned rounds without executions only')
    # Validate the complete curated list before creating output.
    copies = [(local_file(review, e['path']), e['destination'], e) for e in spec['files']]
    reserved = {'index.html', 'report.html', 'report.md', 'bundle_manifest.json',
                'metadata/round.yaml', 'metadata/harness.json', 'maps/index.html'}
    names = set(reserved)
    for _, name, entry in copies:
        rel = PurePosixPath(name)
        if rel.is_absolute() or '..' in rel.parts or name in names:
            raise ValueError(f'Unsafe/duplicate bundle destination: {name}')
        names.add(name)
        if entry.get('sha256') != digest(local_file(review, entry['path'])):
            raise ValueError(f'Curated input checksum mismatch: {entry["path"]}')
    destination.mkdir(parents=True)
    for folder in ('metadata', 'figures', 'maps', 'agents', 'inquiry'):
        (destination / folder).mkdir()
    for source, name, _ in copies:
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    shutil.copyfile(round_file, destination / 'metadata/round.yaml')
    agent_links = []
    plan_hashes = {}
    for instance in record['instances']:
        name = instance['id']
        if not name.replace('-', '').isalnum():
            raise ValueError('Unsafe instance ID')
        node = next(n for n in record['graph']['nodes'] if n.get('instance') == name)
        assignment = local_file(review, instance['assignment'])
        sha = digest(assignment)
        if sha != node['step_plan']['plan_sha256']:
            raise ValueError(f'Step-plan checksum mismatch: {name}')
        plan_hashes[name] = sha
        folder = destination / 'agents' / name
        folder.mkdir()
        # Keep the round's relative assignment/round-only-role references resolvable.
        frozen_assignment = destination / 'metadata' / instance['assignment']
        frozen_assignment.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(assignment, frozen_assignment)
        if instance.get('role_scope') == 'round_only':
            role = local_file(review, instance['role'])
            frozen_role = destination / 'metadata' / instance['role']
            frozen_role.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(role, frozen_role)
        plan = assignment.read_text()
        (folder / 'plan.md').write_text(plan)
        (folder / 'report.md').write_text('Not run. No observations or scientific findings from this role.\n')
        dump(folder / 'execution.json', {'status': 'not_run', 'actual_executions': []})
        (folder / 'index.html').write_text(page(name, f'<h1>{name}: planned only</h1><p><a href="../../index.html">Index</a></p>'
            '<p>Approval: pending. <a href="plan.md">Plan manuscript</a> · <a href="execution.json">Execution record: not_run</a></p>'
            '<pre>' + html.escape(plan) + '</pre>'))
        agent_links.append(f'<li><a href="agents/{name}/index.html">{name}</a> — pending, not run</li>')
    dump(destination / 'metadata/harness.json', {'status': 'not_run', 'instances': [
        {'id': i['id'], 'host_planned': i['host_planned'], 'delegation': i['delegation'],
         'assignment_sha256': plan_hashes[i['id']], 'actual_executions': []}
        for i in record['instances']],
        'limitations': ['No native delegated subagent is claimed. Planning/build checks are not role executions.']})
    report = spec['report_markdown'] + '\n\n' + NON_CLAIMS + '\n'
    (destination / 'report.md').write_text(report)
    (destination / 'report.html').write_text(page('Private planned report',
        '<h1>Private planning draft — not a scientific result</h1><p><a href="index.html">Index</a> · '
        '<a href="maps/index.html">Offline map</a> · <a href="report.md">Manuscript</a></p><pre>' + html.escape(report) + '</pre>'))
    layers = spec['map_layers']
    for layer in layers:
        local_file(destination, layer['file'])
    rois = json.loads(local_file(destination, 'metadata/rois.geojson').read_text())
    payload = json.dumps({'rois': rois, 'layers': layers}).replace('<', '\\u003c')
    script = '''const d=PAYLOAD; const map=L.map('map'); window.bundleMap=map;
const overlays={}; const group=L.geoJSON(d.rois,{style:f=>({color:f.properties.id.startsWith('CONTROL')?'#37b7ff':'#ffd400',weight:3,fillOpacity:0.05}),
onEachFeature:(f,l)=>l.bindTooltip(f.properties.id+' — archived sampling polygon; QA pending')}).addTo(map);
for(const x of d.layers){overlays[x.label]=L.imageOverlay('../'+x.file,x.bounds,{opacity:1,
attribution:'Copernicus Sentinel-2 / Earth Search, Element 84; archived context, dates in selector'});}
const values=Object.values(overlays); if(values.length)values[0].addTo(map);
L.control.layers(overlays,{'Archived ROIs and controls (QA pending)':group},{collapsed:false}).addTo(map);
L.control.scale().addTo(map); map.fitBounds(group.getBounds()); window.bundleLayers=overlays;
'''.replace('PAYLOAD', payload)
    unavailable = html.escape('; '.join(spec['unavailable_layers']))
    (destination / 'maps/index.html').write_text(page('Offline archived context',
        '<h1>Archived single-scene context — monthly analysis not run</h1><p><a href="../index.html">Index</a>. '
        'Switch archived dates with the layer selector. Yellow: candidates; blue: visual controls, stability unverified. '
        'Transparent image pixels are unavailable, not unchanged.</p><p>Not available: ' + unavailable + '</p>'
        '<link rel="stylesheet" href="leaflet.css"><script src="leaflet.js"></script>'
        '<div id="map" style="height:70vh;background:#666"></div><script>' + script + '</script>'))
    figures = ''.join(f'<li><a href="{html.escape(e["destination"], quote=True)}">'
                      f'{html.escape(e.get("label", e["destination"]))}</a></li>'
                      for _, _, e in copies if e['destination'].startswith('figures/'))
    (destination / 'index.html').write_text(page('Private planned-only investigation',
        '<h1>Private planned-only investigation</h1><p>All graph/step/release approvals pending. Seven roles not run.</p>'
        '<p><a href="report.html">Report and open issues</a> · <a href="maps/index.html">Offline Leaflet viewer</a> · '
        '<a href="metadata/graph.svg">Canonical graph SVG</a> · <a href="metadata/graph.mmd">Mermaid</a> · '
        '<a href="bundle_manifest.json">Hash manifest</a></p><img src="metadata/graph.svg" alt="Canonical planned graph">'
        '<h2>Seven plans</h2><ul>' + ''.join(agent_links) + '</ul><h2>Source PNGs</h2><ul>' + figures + '</ul><p>' + NON_CLAIMS + '</p>'))
    # Create the manifest target before auditing navigation, then replace its content.
    dump(destination / 'bundle_manifest.json', {})
    links = audit_links(destination)
    aoi = json.loads((destination / 'metadata/aoi.geojson').read_text())
    geometry = ({'type': 'GeometryCollection', 'geometries': [f['geometry'] for f in aoi['features']]}
                if aoi['type'] == 'FeatureCollection' else aoi['geometry'] if aoi['type'] == 'Feature' else aoi)
    geometry_digest = hashlib.sha256(json.dumps(geometry, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    manifest = {**spec['metadata'], 'version': '1.0', 'status': 'private_planned_draft',
                'review_decision': 'pending', 'upstream_commits': record['repos'],
                'aoi_geometry_sha256': geometry_digest,
                'aoi_source_file_sha256': digest(destination / 'metadata/aoi.geojson'),
                'aoi_digest_convention': 'SHA-256 of geometry-only canonical JSON (sorted keys, compact separators); FeatureCollection becomes ordered GeometryCollection, without union normalization',
                'plan_sha256': plan_hashes,
                'sources': [{k: v for k, v in e.items() if k != 'path'} for _, _, e in copies],
                'checks': [{'name': 'curated input hashes', 'result': 'passed'},
                           {'name': 'step-plan hashes', 'result': 'passed'},
                           {'name': 'HTML/CSS relative dependencies', 'result': 'passed', 'count': links}],
                'limitations': ['Local packaging checks are not scientific verification or release approval.',
                                'Monthly rasters, forest mask and dated independent before/after evidence are absent.'],
                'files': [{'path': p.relative_to(destination).as_posix(), 'size_bytes': p.stat().st_size,
                           'sha256': digest(p)} for p in sorted(destination.rglob('*'))
                          if p.is_file() and p != destination / 'bundle_manifest.json']}
    dump(destination / 'bundle_manifest.json', manifest)
    result = verify_bundle(destination)
    with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED) as z:
        for p in sorted(destination.rglob('*')):
            if p.is_file():
                z.write(p, p.relative_to(destination).as_posix())
    return {'destination': str(destination), 'zip': str(archive), **result}


def build_bundle(review, destination):
    """Stage and verify privately, exposing a complete draft only on success."""
    review, destination = Path(review).resolve(), Path(destination).resolve()
    archive = destination.with_suffix('.zip')
    if destination.exists() or archive.exists():
        raise ValueError('Choose a new destination; existing bundles are immutable')
    if destination.is_relative_to(review):
        raise ValueError('Bundle output must be separate from the review inputs')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.bundle-staging-', dir=destination.parent) as temp:
        staged = Path(temp) / 'draft'
        result = _build_draft(review, staged)
        if destination.exists() or archive.exists():
            raise ValueError('Choose a new destination; existing bundles are immutable')
        staged.rename(destination)
        Path(result['zip']).rename(archive)
    return {**result, 'destination': str(destination), 'zip': str(archive)}
