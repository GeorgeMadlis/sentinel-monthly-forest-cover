"""Intersect Metsaregister forest notifications (teatis) with ROI polygons. Usage: python -I intersect_forest_notices.py WORKS_DIR"""
import json, sys, csv
from shapely.geometry import shape
from shapely.ops import transform
from pyproj import Transformer
d = sys.argv[1]
tr = Transformer.from_crs(4326, 3301, always_xy=True).transform
rois = {f['properties']['id']: transform(tr, shape(f['geometry'])) for f in json.load(open(f'{d}/../../inputs/prior_rois.geojson'))['features']}
feats = {}
for sub in ('roi01', 'roi02'):
    for f in json.load(open(f'{d}/downloads/metsaregister/teatis_{sub}.json'))['features']:
        feats[f['properties']['sys_id']] = f
rows = []
for sid, f in feats.items():
    g = shape(f['geometry'])
    if not g.is_valid: g = g.buffer(0)
    p = f['properties']
    for rid, poly in rois.items():
        i = g.intersection(poly).area
        if i < 1: continue
        mrr = g.minimum_rotated_rectangle; xs = list(mrr.exterior.coords)
        import math
        e = sorted([math.dist(xs[0], xs[1]), math.dist(xs[1], xs[2])])
        rows.append({'roi_id': rid, 'teatise_nr': p['teatise_nr'], 'too_kood': p['too_kood'], 'otsus': p['otsus'],
                     'otsus_kinnitatud_kp': (p['otsus_kinnitatud_kp'] or '')[:10], 'kehtiv_kuni': (p['kehtiv_kuni'] or '')[:10],
                     'katastri_nr': p['katastri_nr'], 'pindala_ha_declared': p['pindala'], 'raiutav_maht_m3': p['raiutav_maht'],
                     'notice_area_m2': round(g.area), 'overlap_with_roi_m2': round(i), 'pct_of_notice_in_roi': round(100*i/g.area, 1),
                     'mrr_width_m': round(e[0]), 'mrr_length_m': round(e[1])})
rows.sort(key=lambda r: (r['roi_id'], r['otsus_kinnitatud_kp']))
with open(f'{d}/derived_forest_notices_in_rois.csv', 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
import collections
for rid in rois:
    rr = [r for r in rows if r['roi_id'] == rid]
    print('==', rid, 'notices', len(rr), 'overlap_m2', sum(r['overlap_with_roi_m2'] for r in rr), 'roi_area', round(rois[rid].area))
    c = collections.defaultdict(lambda: [0, 0]);
    for r in rr: k = (r['too_kood'], r['otsus_kinnitatud_kp'][:4]); c[k][0] += 1; c[k][1] += r['overlap_with_roi_m2']
    for k, v in sorted(c.items()): print('  ', k, v)
    for r in rr:
        if r['too_kood'] not in ('HR', 'SR') and (r['overlap_with_roi_m2'] > 5000 or r['mrr_length_m'] > 8*r['mrr_width_m']):
            print('    big/elongated:', {k: r[k] for k in ('teatise_nr','too_kood','otsus','otsus_kinnitatud_kp','katastri_nr','pindala_ha_declared','overlap_with_roi_m2','pct_of_notice_in_roi','mrr_width_m','mrr_length_m')})
