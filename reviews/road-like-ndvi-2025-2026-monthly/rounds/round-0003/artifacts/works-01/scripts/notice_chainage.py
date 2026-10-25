"""Forest-notice overlap (m2) per 1 km bin along simplified ROI centrelines, by work code and approval half-year. Usage: python -I notice_chainage.py WORKS_DIR"""
import json, sys, collections
from shapely.geometry import shape, LineString
from shapely.ops import transform, substring
from pyproj import Transformer
d = sys.argv[1]
tr = Transformer.from_crs(4326, 3301, always_xy=True).transform
rois = {f['properties']['id']: transform(tr, shape(f['geometry'])) for f in json.load(open(f'{d}/../../inputs/prior_rois.geojson'))['features']}
C = {'ROI-01': [(24.5962,58.4266),(24.6410,58.4629),(24.6928,58.4891),(24.7570,58.5137),(24.8146,58.5426)],
     'ROI-02': [(24.5093,58.5853),(24.5111,58.5669),(24.5322,58.5502),(24.5421,58.5270),(24.5394,58.5119)]}
feats = {}
for sub in ('roi01', 'roi02'):
    for f in json.load(open(f'{d}/downloads/metsaregister/teatis_{sub}.json'))['features']: feats[f['properties']['sys_id']] = f
out = {}
for rid, pts in C.items():
    line = transform(tr, LineString(pts)); L = line.length; poly = rois[rid]; s = 0; bins = []
    while s < L:
        slab = poly.intersection(substring(line, s, min(s+1000, L)).buffer(600, cap_style=2))
        c = collections.Counter()
        for f in feats.values():
            g = shape(f['geometry']); g = g if g.is_valid else g.buffer(0)
            a = g.intersection(slab).area
            if a > 1:
                p = f['properties']; dt = (p['otsus_kinnitatud_kp'] or '')[:7]
                half = dt[:4] + ('H1' if dt[5:7] <= '06' else 'H2')
                c[f"{p['too_kood']}_{half}"] += round(a)
        bins.append({'from_m': round(s), 'slab_area_m2': round(slab.area), 'notice_overlap_m2': dict(sorted(c.items()))}); s += 1000
    out[rid] = bins
    print('==', rid)
    for b in bins: print('  ', b)
json.dump(out, open(f'{d}/derived_notice_chainage.json', 'w'), indent=1)
