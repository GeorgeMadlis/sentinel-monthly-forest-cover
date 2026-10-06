"""Local sigma NDVI + same-track Sentinel-1 RTC comparison, without Earth Engine.

Reuses an archived calibrated optical run for its display images and target NDVI.
A bounded, explicitly archived sample estimates optical reference variability.
"""
import argparse
import copy
import html
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from pathlib import Path
import shutil
from zipfile import ZipFile, ZIP_DEFLATED
from urllib.parse import urlsplit

import numpy as np
import rasterio
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from rasterio.windows import Window
from shapely.geometry import shape

from .evidence import load, write_json, checksum, NON_CLAIMS
from .algorithms import aggregate
from .leaflet import prepare_overlays, generate_map
from .pipeline import Workflow
from .providers import ObservationProvider, utc_now
from .raster import read_asset, write_window, tiles, inside
from .selection import rank_key

PC = 'https://planetarycomputer.microsoft.com/api/stac/v1'


def package_original_map(base, out):
    """Keep the comparison independent of the original run's directory."""
    shutil.copytree(Path(base)/'maps', Path(out)/'maps_original', dirs_exist_ok=True)
    return 'maps_original/anomaly_leaflet.html'


def zip_leaflet_comparison(out):
    """Downloadable display artifacts only; exclude satellite source rasters."""
    out = Path(out)
    archive = out/'leaflet-comparison.zip'
    files = [out/'comparison.html', out/'comparison_metrics.json']
    for folder in ('maps_original','maps_fixed_sar','maps_ndvi_sigma','maps'):
        files.extend(p for p in (out/folder).rglob('*') if p.is_file())
    with ZipFile(archive, 'w', compression=ZIP_DEFLATED) as bundle:
        for path in files:
            bundle.write(path, str(Path(out.name)/path.relative_to(out)))
    return archive


def request(method, url, **kwargs):
    with requests.Session() as session:
        retry = Retry(total=4, backoff_factor=1, status_forcelist=[429,500,502,503,504], allowed_methods=['GET','POST'])
        session.mount('https://', HTTPAdapter(max_retries=retry))
        response = session.request(method, url, **kwargs)
        response.raise_for_status()
        return response


@lru_cache(maxsize=8)
def sas_token(account, container):
    response = request('GET', f'https://planetarycomputer.microsoft.com/api/sas/v1/token/{account}/{container}', timeout=60)
    return response.json()['token']


class RasterReader(ObservationProvider):
    def search(self, *args):
        raise NotImplementedError

    def describe_source(self):
        return {'provider': 'archived-and-public-cog'}


def sigma_candidate(current, reference, sigma, count, k):
    """Undefined/zero variability and fewer than two samples are unavailable."""
    valid = (np.isfinite(current) & np.isfinite(reference) & np.isfinite(sigma)
             & (sigma > 0) & (count >= 2))
    return np.where(valid, current-reference < -k*sigma, np.nan).astype('float32')


def radar_candidate(vv_change, vh_change, vv_threshold=-1.5, vh_threshold=-1):
    valid = np.isfinite(vv_change) & np.isfinite(vh_change)
    return np.where(valid, (vv_change < vv_threshold) & (vh_change < vh_threshold), np.nan).astype('float32')


def radar_reference_medians(workflow):
    """Historical confirmation uses median radar on BOTH dates, unlike NDVI mean."""
    inventory = workflow.inventory()
    obs = workflow.config['observations']['sar']
    for window in workflow.windows:
        items = {i['id']:i for q in inventory['queries'] if q['sensor']=='sar'
                 and q['role']=='reference' and q['window_id']==window['id'] for i in q['items']}
        items = sorted(items.values(), key=lambda i:i['id'])
        for tile in tiles(workflow.grid, workflow.size):
            stack = workflow.feature_stack('sar', items, obs, tile)
            gate = inside(workflow.projected, workflow.grid, tile)
            for feature, values in stack.items():
                median = np.where(gate, aggregate(values,'median'), np.nan)
                with rasterio.open(workflow.path(window['id'], feature+'_reference'),'r+') as dst:
                    write_window(dst, median, tile)
    metadata = load(workflow.out/'composites_tiles.json')
    metadata['sar_reference_statistic'] = 'median of selected reference observations in dB'
    write_json(workflow.out/'composites_tiles.json',metadata)


def search_radar(geometry, start, end):
    query = {'collections': ['sentinel-1-rtc'], 'intersects': geometry,
             'datetime': f'{start}T00:00:00Z/{end}T00:00:00Z', 'limit': 100}
    response = request('POST', PC+'/search', json=query, timeout=90)
    data = response.json()
    items = list(data.get('features', []))
    while next((l for l in data.get('links', []) if l['rel'] == 'next'), None):
        link = next(l for l in data['links'] if l['rel'] == 'next')
        response = request(link.get('method', 'GET'), link['href'],
                                    json=link.get('body'), timeout=90)
        response.raise_for_status()
        data = response.json()
        items.extend(data.get('features', []))
    return [i for i in items if start <= i['properties']['datetime'][:10] < end
            and i['properties'].get('sar:instrument_mode') == 'IW'
            and {'VV', 'VH'} <= set(i['properties'].get('sar:polarizations', []))]


def choose_track(groups, geometry, maximum):
    aoi = shape(geometry)
    tracks = []
    for role, items in groups.items():
        for item in items:
            p = item['properties']
            key = (p['sat:orbit_state'], p['sat:relative_orbit'])
            if key not in tracks:
                tracks.append(key)
    options = []
    for key in tracks:
        periods = {}
        for role, items in groups.items():
            # Avoid spatially incomplete scenes and mixing adjacent slices.
            candidates = [i for i in items if (i['properties']['sat:orbit_state'], i['properties']['sat:relative_orbit']) == key
                          and shape(i['geometry']).covers(aoi)]
            unique = {i['properties']['datetime'][:10]: i for i in sorted(candidates, key=lambda i: i['id'])}
            periods[role] = sorted(unique.values(), key=lambda i: i['properties']['datetime'])
        if all(len(v) >= 2 for v in periods.values()):
            options.append((key, periods))
    if not options:
        raise ValueError('No common VV/VH IW track with full AOI coverage and >=2 dates per period')
    key, periods = sorted(options, key=lambda v: (-min(map(len, v[1].values())), -sum(map(len, v[1].values())), v[0]))[0]
    for role, items in periods.items():
        if len(items) > maximum:
            periods[role] = [items[i] for i in np.linspace(0, len(items)-1, maximum).round().astype(int)]
    return key, periods


def materialize(item, keys, grid, out, signed=False):
    result = copy.deepcopy(item)
    result['assets'] = {}
    win = Window(0, 0, grid.width, grid.height)
    for key, source_key in keys.items():
        original = item['assets'][source_key]
        source = {**original, 'scale': .0001 if key in ('red', 'nir') else 1, 'offset': 0}
        path = out/'source_windows'/item['id']/(key+'.tif')
        evidence_path = path.with_suffix('.json')
        expected = {'item_id': item['id'], 'source_url': original['href'],
                    'scale': source['scale'], 'offset': source['offset'],
                    'grid': {'crs': grid.crs, 'transform': list(grid.transform), 'width': grid.width, 'height': grid.height}}
        cached = path.exists() and evidence_path.exists()
        if cached:
            evidence = load(evidence_path)
            cached = all(evidence.get(k) == v for k,v in expected.items()) and evidence.get('sha256') == checksum(path)
        if not cached:
            path.parent.mkdir(parents=True, exist_ok=True)
            if signed:
                url = urlsplit(original['href'])
                token = sas_token(url.hostname.split('.')[0], url.path.strip('/').split('/')[0])
                source['href'] = original['href']+'?'+token.lstrip('?')
            # Do not archive expiring SAS credentials.
            with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR', GDAL_HTTP_MAX_RETRY='3', GDAL_HTTP_RETRY_DELAY='2'):
                values = read_asset(RasterReader(), source, grid, win, categorical=key == 'scl')
            temporary = path.with_suffix('.partial.tif')
            with rasterio.open(temporary, 'w', **grid.profile) as dst:
                write_window(dst, values, win)
            temporary.replace(path)
            write_json(evidence_path, {**expected, 'sha256': checksum(path), 'acquired_at': utc_now(), 'access': 'remote-cog-aoi-window'})
        result['assets'][key] = {'href': str(path.resolve()), 'scale': 1, 'offset': 0,
                                 'source_url': original['href'], 'sha256': checksum(path)}
    print('Ready '+item['id'], flush=True)
    return result


def run(args):
    base = Path(args.optical_run).resolve()
    out = Path(args.output).resolve()
    if out == base or base in out.parents:
        raise ValueError('Use a separate output directory')
    out.mkdir(parents=True, exist_ok=True)
    status = {'status': 'running', 'started_at': utc_now()}
    write_json(out/'execution_status.json', status)
    try:
        selected = load(base/'selected_observations.json')
        for role, record in selected.items():
            for key, asset in record['item']['assets'].items():
                path = base/record['asset_access'][key]['derived_aoi_raster']
                if checksum(path) != record['asset_access'][key]['derived_sha256']:
                    raise ValueError('Archived optical source checksum mismatch')
                asset['href'] = str(path)
        config = copy.deepcopy(load(base/'config_snapshot.json')['configuration'])
        config.update(run_id=out.name, fusion={'mode': 'optical_and_sar'})
        config['temporal']['reference_statistic'] = 'pooled-observations'
        config['threshold'] = {'mode': 'sigma', 'k': args.k, 'min_component_pixels': 1, 'min_valid_pixel_ratio': 0}
        config['output']['prefix'] = str(out)
        # Temporary optical-only setup obtains exactly the archived grid.
        provisional = copy.deepcopy(config)
        provisional['fusion'] = {'mode': 'optical_only'}
        write_json(out/'grid_config.json', provisional)
        write_json(out/'quality_settings.json', {'quality': {'require_min_observations_per_pixel': 1}})
        setup = Workflow(out/'grid_config.json', out/'quality_settings.json', args.aoi, str(out))
        grid = setup.grid
        if not shape(setup.geometry).equals(shape(load(base/'config_snapshot.json')['geometry'])):
            raise ValueError('AOI must match archived optical run')
        ranking = sorted(load(base/'reference_ranking.json'), key=rank_key)
        candidates = [r for r in ranking if r['metrics'].get('aoi_clear_pixel_fraction', 0) >= .5
                      and r['item']['properties'].get('earthsearch:boa_offset_applied') is True]
        dates = set(); optical = []
        for record in candidates:
            date = record['item']['datetime'][:10]
            if date not in dates:
                dates.add(date); optical.append(record['item'])
            if len(optical) == args.reference_scenes:
                break
        if len(optical) < 2:
            raise ValueError('Need at least two clear reference dates for sigma')
        write_json(out/'optical_selection.json', {'policy': 'best AOI quality, >=50% clear per scene, per-pixel SCL masking, unique dates, bounded sample',
                   'maximum': args.reference_scenes, 'items': optical, 'archived_ranking_sha256': checksum(base/'reference_ranking.json')})
        print(f'Acquiring {len(optical)} optical reference dates', flush=True)
        def optical_read(item):
            if item['id'] == selected['reference']['item']['id']:
                return copy.deepcopy(selected['reference']['item'])
            return materialize(item, {'red':'red', 'nir':'nir', 'scl':'scl'}, grid, out)
        with ThreadPoolExecutor(max_workers=3) as pool:
            optical_items = list(pool.map(optical_read, optical))
        write_json(out/'optical_inventory.json', {'items': optical_items+[selected['target']['item']]})
        radar_queries = {}
        for role, dates in [('reference', setup.windows[0]['references'][0]), ('target', setup.windows[0]['target'])]:
            query_path = out/(role+'_radar_query.json')
            if query_path.exists():
                archived = load(query_path)
                if not shape(archived['geometry']).equals(shape(setup.geometry)) or archived['dates'] != list(dates):
                    raise ValueError('Cached radar query has different AOI/period')
                radar_queries[role] = archived['items']
            else:
                radar_queries[role] = search_radar(setup.geometry, *dates)
                write_json(query_path, {'geometry': setup.geometry, 'dates': list(dates), 'queried_at': utc_now(), 'endpoint': PC, 'items': radar_queries[role]})
        track, periods = choose_track(radar_queries, setup.geometry, args.radar_scenes)
        write_json(out/'radar_selection.json', {'track': list(track), 'policy': 'common full-coverage IW VV/VH track; unique dates; uniform temporal sample if capped', 'maximum_per_period': args.radar_scenes,
                  'periods': {r:[i['id'] for i in items] for r,items in periods.items()}})
        radar = [i for items in periods.values() for i in items]
        print(f'Acquiring {len(radar)} radar dates on {track}', flush=True)
        def radar_read(raw):
            item = {'id': raw['id'], 'datetime': raw['properties']['datetime'], 'geometry': raw['geometry'],
                    'properties': raw['properties'], 'assets': raw['assets']}
            return materialize(item, {'VV':'vv', 'VH':'vh'}, grid, out, signed=True)
        with ThreadPoolExecutor(max_workers=3) as pool:
            radar_items = list(pool.map(radar_read, radar))
        write_json(out/'radar_inventory.json', {'items': radar_items})
        config['providers'] = {'optical': {'type':'local', 'collection':'archived-calibrated-s2', 'inventory':'optical_inventory.json'},
                               'sar': {'type':'local', 'collection':'planetary-computer-sentinel-1-rtc', 'inventory':'radar_inventory.json'}}
        config['observations']['sar'] = {'dataset':'DS-0003', 'version':'Planetary Computer sentinel-1-rtc; item provenance archived',
                 'features':['VV','VH'], 'units':'linear', 'aggregation':'median', 'thresholds':{'VV':args.vv_drop, 'VH':args.vh_drop},
                 'preprocessing':{'orbit_direction':track[0], 'relative_orbit':track[1], 'instrument_mode':'IW',
                                  'terrain_flattening':'provider radiometric terrain correction', 'speckle_treatment':'temporal median in dB; no spatial filter'}}
        write_json(out/'workflow.json', config)
        workflow = Workflow(out/'workflow.json', out/'quality_settings.json', args.aoi, str(out))
        print('Calculating local composites and changes', flush=True)
        workflow.run('composites')
        radar_reference_medians(workflow)
        workflow.run('anomaly')
        def read(name):
            with rasterio.open(workflow.path('w0000', name)) as src:
                return src.read(1, masked=True).filled(np.nan)
        opt = sigma_candidate(read('NDVI_current'), read('NDVI_reference'), read('NDVI_reference_std'), read('NDVI_reference_count'), args.k)
        # Ensure the production sigma decision has the same explicit minimum evidence.
        std_path = workflow.path('w0000', 'NDVI_reference_std')
        sigma = read('NDVI_reference_std')
        sigma[~np.isfinite(opt)] = np.nan
        with rasterio.open(std_path, 'r+') as dst:
            write_window(dst, sigma, Window(0,0,grid.width,grid.height))
        workflow.run('area'); workflow.run('report')
        radar_mask = radar_candidate(read('VV_change'), read('VH_change'), args.vv_drop, args.vh_drop)
        combined = read('disturbance')
        expected = np.where(np.isfinite(opt) & np.isfinite(radar_mask), (opt == 1) & (radar_mask == 1), np.nan)
        if not np.allclose(combined, expected, equal_nan=True):
            raise ValueError('Workflow result differs from the explicit three-test decision')
        original = base/'w0000'/'disturbance.tif'
        with rasterio.open(original) as src:
            old = src.read(1, masked=True).filled(np.nan)
        # Third control holds the original fixed optical test constant.
        fixed_fused = np.where(np.isfinite(old) & np.isfinite(radar_mask), (old == 1) & (radar_mask == 1), np.nan)
        radar_rule = f'ΔVV < {args.vv_drop:g} dB AND ΔVH < {args.vh_drop:g} dB'
        maps = [('maps', read('disturbance'), 'NDVI decrease < −k × reference σ AND '+radar_rule, True),
                ('maps_ndvi_sigma', opt, 'NDVI decrease < −k × reference σ; optical-only control', False),
                ('maps_fixed_sar', fixed_fused, 'Original fixed NDVI decrease < −0.2 AND '+radar_rule, True)]
        metrics = {'original': {'anomaly_pixels':int(np.count_nonzero(old==1)),
                               'valid_pixels':int(np.count_nonzero(np.isfinite(old))),
                               'anomaly_ha':round(float(np.count_nonzero(old==1)*grid.pixel_ha),2)}}
        metadata = {'run_id':out.name, 'k':args.k, 'radar_thresholds_db':{'VV':args.vv_drop,'VH':args.vh_drop},
             'radar_track':list(track), 'radar_dates':{r:[i['properties']['datetime'] for i in items] for r,items in periods.items()},
             'optical_reference_dates':[i['datetime'] for i in optical_items], 'optical_target':selected['target']['item']['datetime'],
             'reference_policy':'pooled observations, bounded best-quality sample; target is original selected scene',
             'sar_reference_statistic':'median of selected reference observations in dB; target also median',
             'sigma_validity':'>=2 finite reference NDVI observations and strictly positive population standard deviation',
             'forest_mask':None, 'non_claims':NON_CLAIMS, 'comparison_note':'RGB backgrounds identical to original. Sigma optical reference differs from the original single-scene reference.',
             'source_run':str(base), 'rgb':'B04/B03/B02 reflectance 0–0.3, gamma 2.2',
             'qa_limitations':['Ungated all-land-cover screening', 'Reference sigma includes within-summer vegetation variation', 'Bounded scene sampling', 'No spatial speckle filter; temporal median only', 'Radar summarizes the whole summer; target optical NDVI is a single June observation']}
        for folder, values, method, fused in maps:
            layer = out/(folder+'_mask.tif')
            with rasterio.open(layer,'w',**grid.profile) as dst:
                write_window(dst, values, Window(0,0,grid.width,grid.height))
            directory = out/folder; directory.mkdir(exist_ok=True)
            for name in ('leaflet.js','leaflet.css','images'):
                source = base/'maps'/name
                if source.is_dir():
                    shutil.copytree(source,directory/name,dirs_exist_ok=True)
                else:
                    shutil.copy2(source,directory/name)
            bounds = prepare_overlays(directory, workflow.geometry, selected, RasterReader(), layer)
            for role in selected:
                if checksum(directory/(role+'.png')) != checksum(base/'maps'/(role+'.png')):
                    raise ValueError('RGB background differs from original map')
            metric = {'anomaly_pixels':int(np.count_nonzero(values==1)), 'valid_pixels':int(np.count_nonzero(np.isfinite(values))),
                      'anomaly_ha':round(float(np.count_nonzero(values==1)*grid.pixel_ha),2)}
            metrics[folder] = metric
            md = {**metadata, 'method':method, 'metrics':metric,
                  'threshold':{'mode':'fixed','value':-.2} if folder=='maps_fixed_sar' else config['threshold'],
                  'legend':'Red: NDVI decrease with both VV and VH radar decreases; transparent: no candidate or unavailable data.' if fused else 'Red: NDVI decrease exceeding the sigma threshold; transparent: no candidate or unavailable data.'}
            generate_map(directory/'anomaly_leaflet.html',workflow.geometry,bounds,selected,md)
            write_json(directory/'map_metadata.json', md)
        write_json(out/'comparison_metrics.json', metrics)
        original_link = package_original_map(base, out)
        choices = [(original_link, 'Original: fixed NDVI'),
                   ('maps_fixed_sar/anomaly_leaflet.html', 'Fixed NDVI + Sentinel-1'),
                   ('maps_ndvi_sigma/anomaly_leaflet.html', 'Sigma NDVI only'),
                   ('maps/anomaly_leaflet.html', 'Sigma NDVI + Sentinel-1')]
        options = ''.join('<option value="'+html.escape(url, quote=True)+'">'+html.escape(label)+'</option>' for url,label in choices)
        (out/'comparison.html').write_text('''<!doctype html><html><head><meta charset="utf-8"><title>Compare satellite anomaly maps</title>
<style>body{margin:0;font:14px sans-serif}header{padding:12px}main{display:flex;height:calc(100vh - 100px)}section{width:50%;display:flex;flex-direction:column}select{padding:8px}iframe{border:0;flex:1;width:100%}</style></head><body>
<header><b>Compare anomaly methods</b><p>Same RGB images, area and map scale. Choose each method below. Fixed NDVI comparisons isolate radar confirmation; sigma comparisons use a multi-image reference.</p></header>
<main><section><select id="left">'''+options+'''</select><iframe id="leftMap" title="Left comparison"></iframe></section>
<section><select id="right">'''+options+'''</select><iframe id="rightMap" title="Right comparison"></iframe></section></main>
<script>for(const id of ['left','right']){const s=document.getElementById(id),f=document.getElementById(id+'Map');s.selectedIndex=id==='left'?0:1;const update=()=>f.src=s.value;s.addEventListener('change',update);update();}</script></body></html>''')
        manifest = load(out/'run_manifest.json')
        manifest.update(comparison=metadata, comparison_metrics=metrics,
                        source_code_sha256=checksum(Path(__file__)),
                        comparison_artifacts={**{folder:folder+'/anomaly_leaflet.html' for folder, *_ in maps},
                                              'original':original_link, 'download':'leaflet-comparison.zip'})
        write_json(out/'run_manifest.json', manifest)
        zip_leaflet_comparison(out)
        status.update(status='completed', metrics=metrics)
        print(metrics, flush=True)
    except Exception as exc:
        status.update(status='failed', error_type=type(exc).__name__, error=str(exc).split('?')[0])
        raise
    finally:
        status['finished_at'] = utc_now()
        write_json(out/'execution_status.json', status)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--optical-run', default='runs/aoi-s2-jja-2025-2026-calibrated')
    parser.add_argument('--output', default='runs/aoi-s2-s1-jja-2025-2026-sigma')
    parser.add_argument('--aoi', default='configs/aoi.example.geojson')
    parser.add_argument('--k', type=float, default=2)
    parser.add_argument('--reference-scenes', type=int, default=8)
    parser.add_argument('--radar-scenes', type=int, default=12)
    parser.add_argument('--vv-drop', type=float, default=-1.5)
    parser.add_argument('--vh-drop', type=float, default=-1)
    args = parser.parse_args()
    if not np.isfinite(args.k) or args.k <= 0 or args.reference_scenes < 2 or args.radar_scenes < 2:
        parser.error('Require finite positive k and >=2 reference/radar scenes')
    if not all(np.isfinite(v) and v < 0 for v in (args.vv_drop,args.vh_drop)):
        parser.error('Radar drop thresholds must be finite and negative')
    run(args)


if __name__ == '__main__':
    main()
