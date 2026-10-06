"""Stage-separated tiled executor. Intermediate rasters are durable evidence."""
from contextlib import ExitStack
from datetime import datetime, timezone
import csv
import json
from pathlib import Path
import platform

import numpy as np
import rasterio
from PIL import Image
from pyproj import __version__ as pyproj_version
from shapely.geometry import box, mapping, shape
from rasterio.warp import transform_geom

from . import __version__
from .algorithms import OPTICAL, aggregate, clean, feature, fuse
from .config import read_config
from .evidence import NON_CLAIMS, checksum, geometry_hash, load, write_json
from .providers import provider, utc_now
from .raster import (aoi_geometry, expand, grid_for, inside, read_asset,
                     tiles, write_window)
from .temporal import windows

ROOT = Path(__file__).resolve().parents[1]


class Workflow:
    def __init__(self, manifest, forest_def, aoi, output_prefix=None):
        self.config = read_config(manifest)
        self.forest_def = load(forest_def)
        self.geometry = aoi_geometry(load(aoi))
        self.grid, self.projected = grid_for(self.geometry, self.config['execution'])
        self.out = Path(output_prefix or self.config['output']['prefix'])
        self.out.mkdir(parents=True, exist_ok=True)
        self.providers = {s: provider(p) for s, p in self.config['providers'].items() if s in self.config['observations']}
        self.windows = windows(self.config)
        self.size = self.config['execution']['tile_size']
        self.signature = geometry_hash({'config': self.config, 'forest_definition': self.forest_def, 'geometry': self.geometry})

    def path(self, wid, name):
        return self.out / wid / (name + '.tif')

    def discovery(self):
        snapshot_path = self.out / 'config_snapshot.json'
        if snapshot_path.exists() and load(snapshot_path).get('signature') != self.signature:
            raise ValueError('Output directory belongs to a different configuration/AOI; choose a new output prefix')
        write_json(snapshot_path, {'signature': self.signature, 'configuration': self.config,
                                  'forest_definition': self.forest_def, 'geometry': self.geometry})
        inventory = {'signature': self.signature, 'windows': self.windows, 'queries': [],
                     'forest_mask_sha256': checksum(self.config['forest_mask']['path'])}
        fingerprints = {}
        raster_metadata = {}
        for w in self.windows:
            for sensor, obs in self.config['observations'].items():
                p = self.providers[sensor]
                filters = self.config['providers'][sensor].get('filters', {})
                for role, periods in [('target', [w['target']]), ('reference', w['references'])]:
                    for index, (start, end) in enumerate(periods):
                        items = p.search(self.geometry, start, end, filters)
                        if len(items) > self.config['execution']['max_observations_per_window']:
                            raise ValueError('Observation limit exceeded; shorten windows or explicitly increase bounded tile stack budget')
                        if sensor == 'sar':
                            self.validate_sar(items, obs)
                        # Fingerprint local raster inputs. Remote checksums/ETags are retained if supplied by STAC.
                        for item in items:
                            for asset in item['assets'].values():
                                href = asset['href']
                                if href not in raster_metadata:
                                    with p.open_asset(asset) as src:
                                        if not src.crs:
                                            raise ValueError(f'Asset lacks CRS: {href}')
                                        raster_metadata[href] = {'crs': str(src.crs), 'resolution': list(src.res),
                                            'nodata': src.nodata if src.nodata is None or np.isfinite(src.nodata) else 'NaN',
                                            'block_shapes': [list(b) for b in src.block_shapes]}
                                asset['source_raster'] = raster_metadata[href]
                                if not '://' in href:
                                    if href not in fingerprints:
                                        fingerprints[href] = checksum(href)
                                    asset['sha256'] = fingerprints[href]
                                    asset['source_modified_time_utc'] = datetime.fromtimestamp(Path(href).stat().st_mtime, timezone.utc).isoformat()
                        query = p.record_query(self.geometry, start, end, filters, items)
                        inventory['queries'].append({**query, 'window_id': w['id'], 'sensor': sensor, 'role': role, 'period_index': index})
        write_json(self.out / 'observation_inventory.json', inventory)
        write_json(self.out / 'composites_metadata.json', {'run_id': self.config['run_id'], 'windows': self.windows,
                   'dataset_ids': {s: o['dataset'] for s, o in self.config['observations'].items()}})
        return inventory

    @staticmethod
    def validate_sar(items, obs):
        prep = obs['preprocessing']
        for i in items:
            props = i.get('properties', {})
            expected = {'sat:orbit_state': prep['orbit_direction'], 'sat:relative_orbit': prep['relative_orbit'],
                        'sar:instrument_mode': prep['instrument_mode']}
            if any(props.get(k) != v for k, v in expected.items()):
                raise ValueError(f"Incompatible/missing SAR acquisition geometry for {i['id']}")
            if not {'VV', 'VH'} <= set(props.get('sar:polarizations', [])):
                raise ValueError(f"Missing VV/VH acquisition metadata for {i['id']}")

    def inventory(self):
        data = load(self.out / 'observation_inventory.json')
        if data['signature'] != self.signature:
            raise ValueError('Stale discovery inventory; rerun build_monthly_composites')
        if checksum(self.config['forest_mask']['path']) != data['forest_mask_sha256']:
            raise ValueError('Forest baseline changed after discovery; start a new run')
        return data

    def feature_stack(self, sensor, items, obs, window):
        count = len(items)
        dims = (int(window.height), int(window.width))
        stacks = {f: np.full((max(count, 1), *dims), np.nan, dtype='float32') for f in obs['features']}
        needed = set()
        for f in obs['features']:
            needed.update(OPTICAL[f] if sensor == 'optical' else ('VV', 'VH') if f == 'VV_MINUS_VH_DB' else (f,))
        for index, item in enumerate(items):
            missing = needed - item['assets'].keys()
            if missing:
                raise ValueError(f"{item['id']} lacks named assets {sorted(missing)}")
            bands = {b: read_asset(self.providers[sensor], item['assets'][b], self.grid, window) for b in needed}
            if sensor == 'optical':
                quality = obs['quality']
                if quality['mode'] == 'scl':
                    scl = read_asset(self.providers[sensor], item['assets']['scl'], self.grid, window, categorical=True)
                    valid = np.isin(scl, quality.get('valid_classes', [4, 5, 6, 7]))
                    bands = {b: np.where(valid, v, np.nan) for b, v in bands.items()}
                elif quality['mode'] != 'pre-masked' or not quality.get('description'):
                    raise ValueError('Quality must be scl or documented pre-masked')
            for f in obs['features']:
                stacks[f][index] = feature(f, bands, obs.get('units', 'db'))
        return stacks

    def composites(self):
        inventory = self.inventory()
        seen = set()
        for query in inventory['queries']:
            for item in query['items']:
                for asset in item['assets'].values():
                    href = asset['href']
                    if 'sha256' in asset and href not in seen:
                        if checksum(href) != asset['sha256']:
                            raise ValueError('Raster input changed after discovery; start a new run')
                        seen.add(href)
        minimum = int(self.forest_def.get('quality', {}).get('require_min_observations_per_pixel', 1))
        if minimum < 1:
            raise ValueError('Minimum observation count must be positive')
        for w in self.windows:
            with ExitStack() as ctx:
                writers = {}
                for sensor, obs in self.config['observations'].items():
                    for f in obs['features']:
                        for suffix in ('current', 'reference', 'reference_std', 'current_count', 'reference_count'):
                            path = self.path(w['id'], f'{f}_{suffix}')
                            path.parent.mkdir(parents=True, exist_ok=True)
                            writers[(f, suffix)] = ctx.enter_context(rasterio.open(path, 'w', **self.grid.profile))
                for tile in tiles(self.grid, self.size):
                    gate = inside(self.projected, self.grid, tile)
                    for sensor, obs in self.config['observations'].items():
                        queries = [q for q in inventory['queries'] if q['window_id'] == w['id'] and q['sensor'] == sensor]
                        current_items = next(q['items'] for q in queries if q['role'] == 'target')
                        ref_queries = sorted((q for q in queries if q['role'] == 'reference'), key=lambda q: q['period_index'])
                        method = obs.get('aggregation', self.config['temporal']['aggregation'])
                        current = self.feature_stack(sensor, current_items, obs, tile)
                        # Read one reference period at a time. Bound total pooled stacks explicitly.
                        if self.config['temporal'].get('reference_statistic', 'period-composites') == 'pooled-observations':
                            ref_items = {i['id']: i for q in ref_queries for i in q['items']}
                            if len(ref_items) > self.config['execution']['max_observations_per_window']:
                                raise ValueError('Pooled reference observation limit exceeded')
                            references = self.feature_stack(sensor, sorted(ref_items.values(), key=lambda i: i['id']), obs, tile)
                            ref_counts = {f: np.sum(np.isfinite(s), axis=0) for f, s in references.items()}
                        else:
                            references = {f: [] for f in obs['features']}
                            ref_counts = {f: np.zeros(gate.shape, dtype='int32') for f in obs['features']}
                            for q in ref_queries:
                                stack = self.feature_stack(sensor, q['items'], obs, tile)
                                for f, s in stack.items():
                                    n = np.sum(np.isfinite(s), axis=0)
                                    ref_counts[f] += n
                                    references[f].append(np.where(n >= minimum, aggregate(s, method), np.nan))
                            references = {f: np.stack(s) for f, s in references.items()}
                        for f, s in current.items():
                            cur_count = np.sum(np.isfinite(s), axis=0)
                            cur = np.where(cur_count >= minimum, aggregate(s, method), np.nan)
                            ref = np.where(ref_counts[f] >= minimum, aggregate(references[f], 'mean'), np.nan)
                            std = np.where(ref_counts[f] >= minimum, aggregate(references[f], 'std'), np.nan)
                            for suffix, values in [('current', cur), ('reference', ref), ('reference_std', std), ('current_count', cur_count), ('reference_count', ref_counts[f])]:
                                write_window(writers[(f, suffix)], np.where(gate, values, np.nan), tile)
        write_json(self.out / 'composites_tiles.json', {'run_id': self.config['run_id'], 'window_count': len(self.windows),
                   'tile_size_pixels': self.size, 'reference_statistic': self.config['temporal'].get('reference_statistic', 'period-composites')})

    def anomalies(self):
        self.inventory()
        for w in self.windows:
            for obs in self.config['observations'].values():
                for f in obs['features']:
                    with rasterio.open(self.path(w['id'], f'{f}_current')) as cur, rasterio.open(self.path(w['id'], f'{f}_reference')) as ref, rasterio.open(self.path(w['id'], f'{f}_change'), 'w', **self.grid.profile) as dst:
                        for tile in tiles(self.grid, self.size):
                            values = cur.read(1, window=tile, masked=True).filled(np.nan)-ref.read(1, window=tile, masked=True).filled(np.nan)
                            write_window(dst, values, tile)
        write_json(self.out / 'ndvi_anomaly_summary.json', {'run_id': self.config['run_id'], 'convention': 'current-minus-reference', 'windows': self.windows})

    def candidates(self):
        inventory = self.inventory()
        rows = []
        threshold = self.config['threshold']
        minimum = int(threshold.get('min_component_pixels', 1))
        halo = minimum - 1
        if halo > self.size:
            raise ValueError('Component halo exceeds tile budget; increase tile_size or reduce min_component_pixels')
        fm = self.config['forest_mask']
        forest = {'href': fm['path'], 'band': fm.get('band', 1)}
        for w in self.windows:
            with ExitStack() as ctx:
                inputs = {}
                for sensor, obs in self.config['observations'].items():
                    for f in obs['features']:
                        inputs[f] = ctx.enter_context(rasterio.open(self.path(w['id'], f'{f}_change')))
                        if sensor == 'optical':
                            inputs[f+'_std'] = ctx.enter_context(rasterio.open(self.path(w['id'], f'{f}_reference_std')))
                names = ('optical_candidate', 'sar_candidate', 'agreement', 'disagreement', 'fused_candidate', 'disturbance')
                outputs = {n: ctx.enter_context(rasterio.open(self.path(w['id'], n), 'w', **self.grid.profile)) for n in names}
                for tile in tiles(self.grid, self.size):
                    win = expand(tile, halo, self.grid)
                    in_aoi = inside(self.projected, self.grid, win)
                    mask_values = read_asset(next(iter(self.providers.values())), forest, self.grid, win, categorical=True)
                    forest_valid = np.isfinite(mask_values)
                    forest_gate = (mask_values >= fm['threshold']) & forest_valid & in_aoi
                    candidates = {}
                    for sensor in ('optical', 'sar'):
                        if sensor not in self.config['observations']:
                            candidates[sensor] = np.full(in_aoi.shape, np.nan, dtype='float32')
                            continue
                        obs = self.config['observations'][sensor]
                        valid = forest_valid & in_aoi
                        flags = []
                        for f in obs['features']:
                            change = inputs[f].read(1, window=win, masked=True).filled(np.nan)
                            valid &= np.isfinite(change)
                            if sensor == 'optical':
                                if threshold['mode'] == 'sigma':
                                    std = inputs[f+'_std'].read(1, window=win, masked=True).filled(np.nan)
                                    tau = -float(threshold['k'])*std
                                    valid &= np.isfinite(std)
                                else:
                                    tau = obs.get('thresholds', {}).get(f, threshold['value'])
                            else:
                                tau = obs['thresholds'][f]
                            flags.append(change < tau)
                        # All selected features must pass; optical indicators retain distinct names/thresholds.
                        candidates[sensor] = np.where(valid, np.logical_and.reduce(flags) & forest_gate, np.nan).astype('float32')
                    fusion = self.config.get('fusion', {'mode': 'optical_only'})
                    fused, agree, disagree = fuse(candidates['optical'], candidates['sar'], **fusion)
                    final = clean(fused, minimum)
                    ys = slice(int(tile.row_off-win.row_off), int(tile.row_off-win.row_off+tile.height))
                    xs = slice(int(tile.col_off-win.col_off), int(tile.col_off-win.col_off+tile.width))
                    core = (ys, xs)
                    core_inside = in_aoi[core]
                    valid_ratio = float(np.count_nonzero(np.isfinite(fused[core]) & core_inside)/max(1, core_inside.sum()))
                    required_ratio = max(float(threshold.get('min_valid_pixel_ratio', 0)), float(self.forest_def.get('quality', {}).get('reject_tile_if_valid_pixel_ratio_below', 0)))
                    accepted = valid_ratio >= required_ratio
                    if not accepted:
                        final[:] = np.nan
                    layers = dict(optical_candidate=candidates['optical'], sar_candidate=candidates['sar'],
                                  agreement=agree, disagreement=disagree, fused_candidate=fused, disturbance=final)
                    for name, values in layers.items():
                        write_window(outputs[name], values[core], tile)
                    if not core_inside.any():
                        continue
                    area = float(np.count_nonzero(final[core] == 1)*self.grid.pixel_ha)
                    bounds = rasterio.windows.bounds(tile, self.grid.transform)
                    geometry = mapping(shape(transform_geom(self.grid.crs, 'EPSG:4326', mapping(box(*bounds)))).intersection(shape(self.geometry)))
                    rows.append({'run_id': self.config['run_id'], 'tile_id': f"{w['id']}_{int(tile.row_off):06d}_{int(tile.col_off):06d}",
                                 'window_id': w['id'], 'month': w['target'][0][:7], 'disturbed_ha': area,
                                 'valid_pixel_ratio': valid_ratio, 'status': 'provisional' if accepted else 'rejected-low-coverage',
                                 'disagreement_pixels': int(np.count_nonzero(disagree[core] == 1)),
                                 's1_confirmation_enabled': 'sar' in self.config['observations'], 'geometry': geometry})
        write_json(self.out / 'loss_area_tiles.json', {'run_id': self.config['run_id'], 'tiles': rows})
        summary = {'run_id': self.config['run_id'], 'tile_count': len(rows), 'windows': []}
        for w in self.windows:
            selected = [r for r in rows if r['window_id'] == w['id']]
            summary['windows'].append({'window_id': w['id'], 'target': w['target'],
                'disturbed_ha_total': sum(r['disturbed_ha'] for r in selected),
                'valid_pixel_ratio_mean': sum(r['valid_pixel_ratio'] for r in selected)/max(1, len(selected)),
                'rejected_tiles': sum(r['status'] != 'provisional' for r in selected)})
        # Never sum overlapping window areas as unique disturbance.
        if len(self.windows) == 1:
            summary.update(summary['windows'][0])
            summary['month'] = self.windows[0]['target'][0][:7]
        write_json(self.out / 'loss_area_summary.json', summary)
        write_json(self.out / 'metrics.json', summary)
        return inventory

    def report(self):
        inventory = self.inventory()
        summary = load(self.out / 'loss_area_summary.json')
        rows = load(self.out / 'loss_area_tiles.json')['tiles']
        fields = [k for k in rows[0] if k != 'geometry'] if rows else ['run_id', 'tile_id', 'disturbed_ha']
        with (self.out / 'loss_area_tiles.csv').open('w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows({k: r[k] for k in fields} for r in rows)
        write_json(self.out / 'loss_area_summary.geojson', {'type': 'FeatureCollection', 'features': [
            {'type': 'Feature', 'geometry': r['geometry'], 'properties': {k:v for k,v in r.items() if k != 'geometry'}} for r in rows]})
        previews = []
        if self.config['output'].get('export_quicklooks', True):
            for w in self.windows:
                with rasterio.open(self.path(w['id'], 'disturbance')) as src:
                    factor = min(1, 512/max(src.width, src.height))
                    arr = src.read(1, out_shape=(max(1, int(src.height*factor)), max(1, int(src.width*factor))), masked=True)
                    rgb = np.zeros((*arr.shape, 3), dtype='uint8')
                    rgb[:] = [40, 110, 40]
                    rgb[np.ma.getmaskarray(arr)] = [160, 160, 160]
                    rgb[arr.filled(-9999) == 1] = [255, 40, 40]
                path = self.out / w['id'] / 'qa.png'
                Image.fromarray(rgb).save(path)
                previews.append(f'<figure><figcaption>{w["id"]}: {w["target"]}</figcaption><img src="{w["id"]}/qa.png"></figure>')
        (self.out / 'report.md').write_text('# Provisional forest disturbance candidates\n\n' + '\n'.join('- '+x for x in NON_CLAIMS) + '\n\n```json\n'+json.dumps(summary, indent=2)+'\n```\n')
        geojson = load(self.out / 'loss_area_summary.geojson')
        # Embedded data supports local-file map viewing without fetching local GeoJSON.
        map_html = '''<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<label>Temporal window <select id="period"></select></label><div id="map" style="height:480px"></div>
<script>const evidence=GEOJSON;
if(window.L){const map=L.map('map');L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
{attribution:'© OpenStreetMap contributors'}).addTo(map);const selector=document.getElementById('period');
for(const id of [...new Set(evidence.features.map(f=>f.properties.window_id))]){const opt=document.createElement('option');opt.value=id;opt.textContent=id;selector.appendChild(opt)}
let layer;function draw(){if(layer)map.removeLayer(layer);layer=L.geoJSON(evidence,{filter:f=>f.properties.window_id===selector.value,
style:f=>({color:f.properties.status==='provisional'?(f.properties.disturbed_ha>0?'#e33':'#284'):'#888',weight:1}),
onEachFeature:(f,l)=>{const p=document.createElement('pre');p.textContent=JSON.stringify(f.properties,null,2);l.bindPopup(p)}}).addTo(map);
if(layer.getLayers().length)map.fitBounds(layer.getBounds())}selector.onchange=draw;draw()}
</script>'''.replace('GEOJSON', json.dumps(geojson).replace('<', '\\u003c'))
        (self.out / 'final_map.html').write_text('<!doctype html><meta charset="utf-8"><title>Forest disturbance evidence</title><h1>Provisional disturbance evidence</h1><p>Red: candidate; green: valid absence; grey: unavailable. '+NON_CLAIMS[0]+'</p><p><a href="loss_area_summary.geojson">Geospatial tile summaries</a> · <a href="run_manifest.json">Manifest</a></p>'+map_html+''.join(previews))
        self.manifest(inventory)

    def manifest(self, inventory):
        descriptor = load(ROOT / 'workflow.yaml')
        fm = self.config['forest_mask']
        methods = ['method:ndvi-anomaly'] if 'NDVI' in self.config['observations'].get('optical', {}).get('features', []) else []
        if 'sar' in self.config['observations']:
            methods.append('method:s1-backscatter-confirmation')
        mode = self.config['temporal']['mode']
        methods.append({'monthly': 'method:monthly-compositing', 'moving-window': 'method:moving-window-comparison',
                        'matched-season': 'method:matched-season-interannual-comparison',
                        'matched-season-moving-window': 'method:matched-season-interannual-comparison'}[mode])
        if mode == 'matched-season-moving-window':
            methods.append('method:moving-window-comparison')
        import scipy
        import yaml
        import PIL
        versions = {'python': platform.python_version(), 'numpy': np.__version__, 'rasterio': rasterio.__version__,
                    'gdal': rasterio.__gdal_version__, 'pyproj': pyproj_version, 'scipy': scipy.__version__, 'PyYAML': yaml.__version__, 'Pillow': PIL.__version__}
        if any(p['type'] == 'stac' for p in self.config['providers'].values()):
            from importlib.metadata import version
            versions['pystac-client'] = version('pystac-client')
        timestamp = inventory['queries'][0]['query_timestamp'] if inventory['queries'] else utc_now()
        data = [{'dataset_name': s, 'source': json.dumps(self.providers[s].describe_source(), sort_keys=True),
                 'inventory_id': o['dataset'], 'dataset_version': o['version'], 'access_time_utc': timestamp,
                 'evidence_role': 'core estimation input'} for s, o in self.config['observations'].items()]
        data.append({'dataset_name': 'baseline forest mask', 'source': fm['path'], 'inventory_id': fm['dataset'],
                     'dataset_version': fm['version'], 'access_time_utc': timestamp, 'evidence_role': 'exclusion mask',
                     'sha256': checksum(fm['path'])})
        artifacts = [{'path': str(p.relative_to(self.out)), 'artifact_type': 'raster' if p.suffix == '.tif' else 'evidence',
                      'sha256': checksum(p)} for p in sorted(self.out.rglob('*')) if p.is_file() and p.name != 'run_manifest.json']
        concepts = [i for i in descriptor['observation_ids'] if not (i == 'observation:sar-backscatter-state' and 'sar' not in self.config['observations'])]
        payload = {'schema_version': '2.0', 'run_id': self.config['run_id'], 'aoi_id': self.config.get('aoi_id', self.config['run_id']),
            'geometry_hash': geometry_hash(self.geometry), 'exchange_crs': 'EPSG:4326',
            'area_method': {'type': 'equal-area', 'unit': 'hectares', 'crs': self.grid.crs, 'pixel_ha': self.grid.pixel_ha},
            'forest_definition': {'name': self.forest_def.get('name', 'external-baseline-mask'), 'baseline_dataset': fm['dataset'],
                'forest_threshold_variable': 'supplied-mask-value', 'forest_threshold_value': fm['threshold'],
                'minimum_mapping_area_ha': self.config['threshold'].get('min_component_pixels', 1)*self.grid.pixel_ha,
                'nodata_policy': 'exclude', 'temporal_interpretation': str(fm['reference_year']),
                'mask_provenance': {**fm, 'sha256': checksum(fm['path'])}},
            'data_provenance': data, 'algorithm': {'name': 'sentinel-forest-disturbance-candidates', 'version': __version__},
            'parameters': self.config, 'temporal_windows': self.windows, 'features_used': {s:o['features'] for s,o in self.config['observations'].items()},
            'selected_item_ids': {sensor: sorted({item['id'] for q in inventory['queries'] if q['sensor'] == sensor for item in q['items']})
                for sensor in self.config['observations']},
            'processing_library_versions': versions,
            'processing_grid': {'crs': self.grid.crs, 'resolution': self.config['execution']['resolution'],
                'transform': list(self.grid.transform)[:6], 'width': self.grid.width, 'height': self.grid.height,
                'nodata': -9999, 'continuous_resampling': 'bilinear', 'mask_resampling': 'nearest', 'tile_size': self.size},
            'outputs': artifacts, 'limitations': NON_CLAIMS + descriptor['divergences'] + self.config.get('migration_notes', []),
            'semantic_provenance': {'schema_version': '1.0', 'methods': [{'id': m, 'version': '1.0'} for m in sorted(set(methods))],
                'knowledge_snapshot': descriptor['knowledge_snapshot'], 'concept_ids': sorted(concepts),
                'dataset_ids': sorted({d['inventory_id'] for d in data}), 'tools': [{'id': 'tool:rasterio', 'version': rasterio.__version__}],
                'workflow': {'id': descriptor['workflow_id'], 'version': __version__},
                'ai_planner_involved': bool(self.config.get('planning_record_id'))}}
        if self.config.get('planning_record_id'):
            payload['semantic_provenance']['planning_record_id'] = self.config['planning_record_id']
        write_json(self.out / 'run_manifest.json', payload)

    def run(self, stage='all'):
        if stage in ('all', 'composites'):
            self.discovery()
            self.composites()
        if stage in ('all', 'anomaly'):
            self.anomalies()
        if stage in ('all', 'area'):
            self.candidates()
        if stage in ('all', 'report'):
            self.report()
