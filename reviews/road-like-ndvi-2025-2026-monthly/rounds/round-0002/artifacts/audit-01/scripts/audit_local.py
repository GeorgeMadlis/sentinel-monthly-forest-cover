"""Read-only cache authentication and reproduction of existing decisions. No discovery."""
import csv
from contextlib import ExitStack
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import warnings

os.environ['PROJ_NETWORK'] = 'OFF'
os.environ['GDAL_DISABLE_READDIR_ON_OPEN'] = 'EMPTY_DIR'
OUT = Path(__file__).resolve().parents[1]
ROOT = OUT.parents[5]
sys.path.insert(0, str(ROOT))
import numpy as np
import rasterio
from rasterio.features import geometry_mask, geometry_window
from rasterio.warp import transform_geom
from rasterio.windows import Window
from shapely.geometry import shape
from PIL import Image, ImageDraw
from scipy.ndimage import binary_erosion
from forest_change.algorithms import feature, aggregate
from forest_change.raster import Grid, tiles, inside, write_window

RUN = ROOT / 'runs/aoi-s2-s1-jja-2025-2026-sigma'
BASE = ROOT / 'runs/aoi-s2-jja-2025-2026-calibrated'
OLD = ROOT / 'reviews/20261006T174722Z-sentinel-road-investigation'


def dump(name, value):
    p = OUT / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def load(p):
    return json.loads(p.read_text())


def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def identifier(p):
    return 'sentinel-local:' + p.relative_to(ROOT).as_posix()


def local(ref):
    if '://' in str(ref) or str(ref).startswith('/vsi'):
        raise ValueError('Network/virtual asset forbidden')
    p = Path(ref).resolve()
    if not p.is_relative_to(ROOT) or not p.is_file():
        raise ValueError('Missing/out-of-scope local cache')
    return p


def inventory():
    before = {}
    for folder in (BASE, RUN, OLD):
        for p in sorted(folder.rglob('*')):
            if p.is_file():
                before[p.relative_to(ROOT).as_posix()] = sha(p)
    dump('originals_before.json', before)
    manifests = []
    authenticated = set()
    for folder in (BASE, RUN):
        m = load(folder / 'run_manifest.json')
        rows = []
        for entry in m['outputs']:
            p = local(folder / entry['path'])
            actual = before[p.relative_to(ROOT).as_posix()]
            match = actual == entry.get('sha256')
            rows.append({'source': identifier(p), 'expected_sha256': entry.get('sha256'),
                         'actual_sha256': actual, 'matches': match})
            if match:
                authenticated.add(p)
        manifests.append({'manifest': identifier(folder / 'run_manifest.json'), 'files': rows,
                          'matches': sum(r['matches'] for r in rows),
                          'mismatches': [r for r in rows if not r['matches']]})
    historical = load(OLD / 'original_hashes_before.json')
    historical_rows = []
    for path, expected in historical.items():
        p = local(path)
        actual = before[p.relative_to(ROOT).as_posix()]
        historical_rows.append({'source': identifier(p), 'expected_sha256': expected,
                                'actual_sha256': actual, 'matches': actual == expected})
    artifact_rows = []
    for path, expected in load(OLD / 'artifact_manifest.json')['artifacts'].items():
        p = OLD / path
        actual = before.get(p.relative_to(ROOT).as_posix())
        artifact_rows.append({'source': identifier(p), 'expected_sha256': expected,
                             'actual_sha256': actual, 'matches': expected == actual})
    dump('cache_authentication.json', {'run_manifests': manifests,
        'historical_original_hashes': historical_rows, 'historical_artifact_hashes': artifact_rows,
        'policy': 'Only original-manifest-matching local raw inputs are consumed for reproduction. Historical derived mismatches are excluded as an original-manifest authority; current bytes and historical hashes retained without rewriting.',
        'limitation': 'Hashes authenticate local byte identity, not provider authenticity or scientific validity.'})
    # Authenticated original-manifest inputs are mandatory, not merely new hashes.
    inv = load(RUN / 'optical_inventory.json')['items']
    radar = load(RUN / 'radar_inventory.json')['items']
    for p in [RUN / 'optical_inventory.json', RUN / 'radar_inventory.json', BASE / 'selected_observations.json']:
        assert p in authenticated, 'Unverified inventory ' + str(p)
    records = []
    for sensor, items in [('optical', inv), ('radar', radar)]:
        for item in items:
            for band, asset in item['assets'].items():
                p = local(asset['href'])
                assert p in authenticated, 'Raw cache not original-manifest authenticated: ' + str(p)
                records.append({'sensor': sensor, 'item_id': item['id'], 'acquisition_utc': item['datetime'],
                    'band': band, 'source': identifier(p), 'sha256': sha(p),
                    'source_url': asset.get('source_url', asset.get('source_asset', {}).get('href')),
                    'calibration_scale': asset.get('scale', 1), 'calibration_offset': asset.get('offset', 0),
                    'lineage': 'Sentinel/Copernicus optical' if sensor == 'optical' else 'Planetary Computer Sentinel-1 RTC'})
    assert all('?' not in (r['source_url'] or '') for r in records), 'Do not retain signed source URLs'
    dump('authenticated_inputs.json', {'assets': records, 'all_original_manifest_match': True})
    print('AUTHENTICATED', len(records), 'local source assets; originals fingerprinted', len(before), flush=True)
    return inv, radar, before


def reproduce(optical, radar):
    geometry = load(ROOT / 'configs/aoi.example.geojson')['features'][0]['geometry']
    with rasterio.open(RUN / 'w0000/NDVI_current.tif') as s:
        grid = Grid(str(s.crs), s.transform, s.width, s.height)
    assert grid.crs == 'EPSG:6933' and grid.pixel_ha == .04
    projected = transform_geom('EPSG:4326', grid.crs, geometry)
    refs = [i for i in optical if i['datetime'].startswith('2025')]
    target = next(i for i in optical if i['datetime'].startswith('2026'))
    single_id = load(BASE / 'selected_observations.json')['reference']['item']['id']
    assert len({i['datetime'][:10] for i in refs}) == len(refs) == 8
    names = ['NDVI_current', 'NDVI_reference', 'NDVI_reference_std', 'NDVI_reference_count',
             'NDVI_change', 'VV_current', 'VV_reference', 'VH_current', 'VH_reference', 'VV_change', 'VH_change']
    comparisons = {n: {'compared_finite_pixels': 0, 'max_absolute_error': 0., 'validity_disagreements': 0} for n in names}
    masks = {'fixed': BASE / 'w0000/disturbance.tif', 'sigma': RUN / 'w0000/optical_candidate.tif',
             'radar': RUN / 'w0000/sar_candidate.tif', 'sigma_and_radar': RUN / 'w0000/disturbance.tif'}
    mask_stats = {n: {'recomputed_candidates': 0, 'archived_candidates': 0,
                     'value_disagreements_common_support': 0, 'validity_disagreements': 0} for n in masks}
    # Never compare revised presentation masks as if they matched the original manifest.
    display_masks = {'sigma': RUN / 'maps_ndvi_sigma_mask.tif', 'fixed_and_radar': RUN / 'maps_fixed_sar_mask.tif',
                     'sigma_and_radar': RUN / 'maps_mask.tif'}
    display_stats = {n: {'current_display_candidates': 0, 'recomputed_candidates': 0,
                        'value_disagreements_common_support': 0, 'validity_disagreements': 0} for n in display_masks}
    cache_metadata = []
    with ExitStack() as stack:
        assets = {}
        for item in optical + radar:
            for key, asset in item['assets'].items():
                p = local(asset['href']);src = stack.enter_context(rasterio.open(p))
                assert (src.crs, src.transform, src.width, src.height) == (rasterio.crs.CRS.from_string(grid.crs), grid.transform, grid.width, grid.height)
                assets[(item['id'], key)] = src
                cache_metadata.append({'item': item['id'], 'band': key, 'grid_crs': str(src.crs),
                    'resolution': list(src.res), 'nodata': src.nodata, 'dtype': src.dtypes[0]})
        old = {n: stack.enter_context(rasterio.open(RUN / 'w0000' / (n + '.tif'))) for n in names}
        old_masks = {n: stack.enter_context(rasterio.open(p)) for n, p in masks.items()}
        display = {n: stack.enter_context(rasterio.open(p)) for n,p in display_masks.items()}
        (OUT / 'recomputed').mkdir(exist_ok=True)
        writers = {n: stack.enter_context(rasterio.open(OUT / 'recomputed' / (n + '.tif'), 'w', **grid.profile))
                   for n in ['fixed', 'sigma', 'radar', 'fixed_and_radar', 'sigma_and_radar']}
        def read(item, key, w):
            asset = item['assets'][key]
            a = assets[(item['id'], key)].read(1, window=w, masked=True).filled(np.nan)
            return a if key == 'scl' else a * asset.get('scale', 1) + asset.get('offset', 0)
        def ndvi(item,w):
            a = feature('NDVI', {b: read(item,b,w) for b in ['nir','red']})
            return np.where(np.isin(read(item,'scl',w), [4,5,6,7]), a, np.nan)
        for w in tiles(grid, 512):
            gate = inside(projected, grid, w)
            refstack = np.stack([ndvi(i,w) for i in refs])
            cur = np.where(gate,ndvi(target,w),np.nan)
            count = np.sum(np.isfinite(refstack),axis=0)
            mean = np.where(gate & (count >= 1),aggregate(refstack,'mean'),np.nan)
            std = np.where(gate & (count >= 2),aggregate(refstack,'std'),np.nan)
            std = np.where(std > 0, std, np.nan)
            count = np.where(gate,count,np.nan)
            delta = cur-mean
            values = {'NDVI_current':cur,'NDVI_reference':mean,'NDVI_reference_std':std,
                      'NDVI_reference_count':count,'NDVI_change':delta}
            for b in ['VV','VH']:
                for role, year in [('current','2026'),('reference','2025')]:
                    observations = [feature(b,{b:read(i,b,w)},units='linear') for i in radar if i['datetime'].startswith(year)]
                    values[b+'_'+role] = np.where(gate,aggregate(np.stack(observations),'median'),np.nan)
                values[b+'_change'] = values[b+'_current']-values[b+'_reference']
            # Production code masks reference_std also where target is missing.
            sigma_valid = np.isfinite(cur)&np.isfinite(mean)&np.isfinite(std)&(std>0)&(count>=2)
            values['NDVI_reference_std'] = np.where(sigma_valid,std,np.nan)
            fixed_delta = cur-ndvi(next(i for i in refs if i['id']==single_id),w)
            decisions = {'fixed':np.where(np.isfinite(fixed_delta),fixed_delta<-.2,np.nan),
                         'sigma':np.where(sigma_valid,delta < -2*std,np.nan)}
            vv,vh=values['VV_change'],values['VH_change'];valid=np.isfinite(vv)&np.isfinite(vh)
            decisions['radar']=np.where(valid,(vv < -1.5)&(vh < -1),np.nan)
            for n in ['fixed','sigma']:
                valid=np.isfinite(decisions[n])&np.isfinite(decisions['radar'])
                decisions[n+'_and_radar']=np.where(valid,(decisions[n]==1)&(decisions['radar']==1),np.nan)
            for n,a in values.items():
                b=old[n].read(1,window=w,masked=True).filled(np.nan);v=np.isfinite(a)&np.isfinite(b);c=comparisons[n]
                c['compared_finite_pixels']+=int(v.sum());c['validity_disagreements']+=int((np.isfinite(a)!=np.isfinite(b)).sum())
                if v.any():c['max_absolute_error']=max(c['max_absolute_error'],float(np.max(np.abs(a[v]-b[v]))))
            for n,a in decisions.items():
                write_window(writers[n],a,w)
                if n in old_masks:
                    b=old_masks[n].read(1,window=w,masked=True).filled(np.nan);c=mask_stats[n];v=np.isfinite(a)&np.isfinite(b)
                    c['recomputed_candidates']+=int((a==1).sum());c['archived_candidates']+=int((b==1).sum())
                    c['value_disagreements_common_support']+=int((a[v]!=b[v]).sum());c['validity_disagreements']+=int((np.isfinite(a)!=np.isfinite(b)).sum())
                if n in display:
                    b=display[n].read(1,window=w,masked=True).filled(np.nan);c=display_stats[n];v=np.isfinite(a)&np.isfinite(b)
                    c['recomputed_candidates']+=int((a==1).sum());c['current_display_candidates']+=int((b==1).sum())
                    c['value_disagreements_common_support']+=int((a[v]!=b[v]).sum());c['validity_disagreements']+=int((np.isfinite(a)!=np.isfinite(b)).sum())
    passed=all(c['max_absolute_error']<=2e-6 and c['validity_disagreements']==0 for c in comparisons.values())
    mask_passed=all(c['value_disagreements_common_support']==0 and c['validity_disagreements']==0 for c in mask_stats.values())
    dump('reproduction.json',{'continuous_rasters':comparisons,'production_masks':mask_stats,
        'unauthenticated_presentation_masks_comparison_only':display_stats,'continuous_tolerance':2e-6,
        'continuous_reproduction_pass':passed,'production_mask_reproduction_pass':mask_passed,
        'formula':'absolute current-minus-reference NDVI, not relative percentage; sigma compares absolute delta to -2 population SD; radar medians in dB',
        'interpretation':'Agreement is a reproducibility result, not road/forest/causal validation.'})
    dump('cache_grid_qa.json',{'assets':cache_metadata,'resampling':'Original materialization: bilinear continuous, nearest SCL; this audit uses exact aligned cached pixels, no further warp.',
        'scl_classes':[4,5,6,7],'mask_dilation':'not applied','source_resolution_limit':'Local analysis caches are 20 m. A 10 m source URL does not make a 20 m derived raster native-resolution evidence.'})
    print('REPRODUCTION',passed,mask_passed,json.dumps(mask_stats),flush=True)


def geometry_and_figures():
    raw=(OLD/'rois.geojson').read_bytes();(OUT/'roi_review.geojson').write_bytes(raw)
    aoi=shape(load(ROOT/'configs/aoi.example.geojson')['features'][0]['geometry'])
    features=load(OUT/'roi_review.geojson')['features'];qa=[]
    (OUT/'inspect/crops').mkdir(parents=True,exist_ok=True)
    with rasterio.open(BASE/'source_windows/target/red.tif') as src:
        grid=Grid(str(src.crs),src.transform,src.width,src.height)
        for f in features:
            g=shape(f['geometry']);projected=transform_geom('EPSG:4326',grid.crs,f['geometry'])
            w=geometry_window(src,[projected],pad_x=5,pad_y=5).round_offsets().round_lengths()
            qa.append({'roi_id':f['properties']['id'],'role':f['properties']['role'],'bounds_wgs84':list(g.bounds),
                'valid':g.is_valid,'within_aoi':aoi.covers(g),'sampling_window_pixels':[int(w.col_off),int(w.row_off),int(w.width),int(w.height)],
                'user_identity_confirmation':f['properties']['id'].startswith('ROI'),
                'uncertainty':f['properties']['uncertainty']})
            panes=[]
            for role in ['reference','target']:
                arrays=[]
                for band in ['red','green','blue']:
                    with rasterio.open(BASE/'source_windows'/role/(band+'.tif')) as s:
                        arrays.append(s.read(1,window=w,masked=True).filled(np.nan))
                rgb=np.stack(arrays,axis=-1);valid=np.all(np.isfinite(rgb),axis=-1)
                pixels=(255*np.power(np.clip(np.nan_to_num(rgb)/.3,0,1),1/2.2)).astype('uint8')
                pixels[~valid]=[100,100,100]
                mask=geometry_mask([projected],out_shape=valid.shape,transform=rasterio.windows.transform(w,grid.transform),invert=True)
                edge=mask&~binary_erosion(mask)
                for overlay in [False,True]:
                    out=pixels.copy()
                    if overlay:out[edge]=[255,220,0] if f['properties']['id'].startswith('ROI') else [0,190,255]
                    img=Image.fromarray(out);img.thumbnail((750,600));panes.append(img)
                    img.save(OUT/'inspect/crops'/f"{f['properties']['id']}-{role}-{'outline' if overlay else 'raw'}.png")
            sheet=Image.new('RGB',(1540,1280),'white');draw=ImageDraw.Draw(sheet)
            labels=['2025-06-15 raw','2025-06-15 sampling outline','2026-06-20 raw','2026-06-20 sampling outline']
            for j,img in enumerate(panes):
                x=(j%2)*770;y=(j//2)*640;draw.text((x+8,y+8),f['properties']['id']+' '+labels[j],fill='black');sheet.paste(img,(x+8,y+30))
            sheet.save(OUT/'inspect'/f"{f['properties']['id']}-qa.png")
    dump('geometry_qa.json',{'source_sha256':sha(OLD/'rois.geojson'),'export_sha256':sha(OUT/'roi_review.geojson'),
        'features':qa,'coordinates_unchanged':True,'centreline_status':'No authoritative centreline file recovered; sampling polygons copied, not reverse-engineered.',
        'limitations':['User identifies the two outlined corridors; this is not surveyed alignment/width or independently confirmed stability of controls.','Visual QA uses 20 m analytical caches.']})
    reg=[]
    for name,col,row in [('Pärnu urban crossing',300,610),('existing road junction',1830,420)]:
        images=[];w=Window(col,row,40,40)
        for role in ['reference','target']:
            arr=[]
            for band in ['red','green','blue']:
                with rasterio.open(BASE/'source_windows'/role/(band+'.tif')) as s:arr.append(s.read(1,window=w,masked=True).filled(np.nan))
            images.append(np.nanmean(np.stack(arr),axis=0))
        a,b=images;scores=[]
        for dy in range(-2,3):
            for dx in range(-2,3):
                x=a[3:-3,3:-3];y=b[3+dy:37+dy,3+dx:37+dx];v=np.isfinite(x)&np.isfinite(y)
                if v.sum()>30:scores.append((float(np.corrcoef(x[v],y[v])[0,1]),dx,dy))
        best=max(scores);reg.append({'landmark':name,'window':[col,row,40,40],'best_integer_shift_pixels':[best[1],best[2]],
            'correlation':best[0],'zero_shift_correlation':next(x[0] for x in scores if x[1:]==(0,0))})
    dump('registration_qa.json',{'checks':reg,'action':'no shift applied','limit':'Two local optical integer shifts only; no subpixel, full-corridor, surveyed or SAR certification.'})


def metadata(optical,radar):
    periods={}
    for name,items in [('optical',optical),('radar',radar)]:
        periods[name]={'dates':[i['datetime'] for i in items], 'unique_days':len({i['datetime'][:10] for i in items}),
            'june_2025_items':sum(i['datetime'].startswith('2025-06') for i in items),
            'june_2026_items':sum(i['datetime'].startswith('2026-06') for i in items)}
    periods['optical']['calibration']='Original source scale 0.0001, offset 0 because earthsearch:boa_offset_applied true; cached reflectance scale 1 offset 0. No second -0.1. Processing baselines 05.11 vs 05.12 for selected reference/target.'
    periods['radar']['track']=load(RUN/'radar_selection.json')['track']
    periods['june_readiness']='Full-AOI selected optical cache has only one June-2026 target. Historical additional June targets are small persistence windows, not full-corridor support. This audit does not generate monthly pairs.'
    dump('observation_dates.json',periods)
    records=[]
    for r in load(OLD/'independent_map_evidence.json')['records']:
        if 'layer_year' not in r:continue
        records.append({'id':r['id'],'layer_year':r['layer_year'],'metadata_date':r.get('metadata_date'),
            'verified_observation_date':r.get('observation_date'),'accessibility':r.get('accessibility'),
            'comparison_side':'unassigned: flight-to-image linkage unresolved' if not r.get('observation_date') else ('pre-July-2025' if r['observation_date']<'2025-07-01' else 'post-July-2025'),
            'date_conflict':r.get('date_conflict'),'source_url':r.get('source_url'),'historical_retrieved_at':r.get('retrieved_at')})
    dump('orthophoto_date_audit.json',{'cutoff':'2025-07-01','records':records,
        'local_post_cutoff_verified':False,'global_post_cutoff_availability':'not_checked_no_remote_access',
        'conclusion':'Relaxed cutoff does not authenticate ambiguous flight dates. Available 2025-layer images may be viewed as undated physical context; no verified before/after timing assertion.'})
    candidates=[]
    for folder in [ROOT/'runs',ROOT/'data',ROOT/'configs']:
        if folder.exists():
            candidates += [identifier(p) for p in folder.rglob('*') if p.is_file() and any(k in p.name.lower() for k in ['hansen','treecover','lossyear','forest_mask'])]
    dump('forest_baseline_audit.json',{'operator_selected':'Hansen GFC 2024 edition','registered_dataset':'DS-0001: Hansen GFC v1.12',
        'local_candidates_by_filename':candidates,'search_scope':['runs/','data/ if present','configs/'],
        'contract_read':'Lab configs/v1_defaults.yaml and specs/v1_forest_baseline.md',
        'limitation':'treecover2000 in the 2024 edition is year-2000 canopy cover, not measured 2024 canopy coverage. Existing Lab v1 defaults declare year_2000_baseline_extent. A 2024 remaining-cover proxy using annual loss requires an explicit reviewed temporal transformation, does not capture all regrowth, and cannot be invented in this audit. No baseline ingestion/download or forest-gated estimates executed.'})


if __name__=='__main__':
    warnings.filterwarnings('ignore',message='Mean of empty slice')
    optical,radar,before=inventory()
    reproduce(optical,radar)
    geometry_and_figures()
    metadata(optical,radar)
    after={p:sha(ROOT/p) for p in before}
    changed=[p for p in before if before[p]!=after[p]]
    dump('originals_after.json',after)
    dump('original_integrity.json',{'files_checked':len(before),'changed':changed,'unchanged':not changed})
    assert not changed,'Original evidence was modified'
    print('ORIGINALS UNCHANGED',len(before),flush=True)
