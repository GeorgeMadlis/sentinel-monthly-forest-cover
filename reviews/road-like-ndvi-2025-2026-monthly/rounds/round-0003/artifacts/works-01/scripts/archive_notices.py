"""Archived forest notices (RD/LR) overlapping ROI polygons, by code and year. Usage: python -I archive_notices.py WORKS_DIR"""
import json, sys, collections, csv
from shapely.geometry import shape
from shapely.ops import transform
from pyproj import Transformer
d = sys.argv[1]
tr = Transformer.from_crs(4326, 3301, always_xy=True).transform
rois = {f['properties']['id']: transform(tr, shape(f['geometry'])) for f in json.load(open(f'{d}/../../inputs/prior_rois.geojson'))['features']}
feats = {}
for sub in ('roi01', 'roi02'):
    for f in json.load(open(f'{d}/downloads/metsaregister/teatis_arhiiv_RD_LR_{sub}.json'))['features']: feats[f['id']] = f
rows = []
for f in feats.values():
    g = shape(f['geometry']); g = g if g.is_valid else g.buffer(0); p = f['properties']
    for rid, poly in rois.items():
        a = g.intersection(poly).area
        if a > 1:
            dt = p.get('otsus_kinnitatud_kp') or p.get('reg_kp') or ''
            rows.append({'roi_id': rid, 'teatise_nr': p.get('teatise_nr'), 'too_kood': p.get('too_kood'), 'otsus': p.get('otsus'), 'otsus_kinnitatud_kp': dt[:10], 'kehtiv_kuni': (p.get('kehtiv_kuni') or '')[:10], 'katastri_nr': p.get('katastri_nr'), 'overlap_with_roi_m2': round(a)})
rows.sort(key=lambda r: (r['roi_id'], r['otsus_kinnitatud_kp']))
if rows:
    with open(f'{d}/derived_archived_notices_in_rois.csv', 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
c = collections.Counter()
for r in rows: c[(r['roi_id'], r['too_kood'], r['otsus'], r['otsus_kinnitatud_kp'][:4])] += r['overlap_with_roi_m2']
for k, v in sorted(c.items()): print(k, v)
for r in rows:
    if r['too_kood'] == 'RD': print('RD', r)
