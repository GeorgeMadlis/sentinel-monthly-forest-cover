"""Profile simplified ROI centrelines (from retask addendum vertices) against reference layers. Usage: python -I profile_centreline.py WORKS_DIR"""
import json, sys
from shapely.geometry import shape, LineString, Point
from shapely.ops import transform, unary_union
from pyproj import Transformer
d = sys.argv[1]
tr = Transformer.from_crs(4326, 3301, always_xy=True).transform
C = {'ROI-01': [(24.5962,58.4266),(24.6410,58.4629),(24.6928,58.4891),(24.7570,58.5137),(24.8146,58.5426)],
     'ROI-02': [(24.5093,58.5853),(24.5111,58.5669),(24.5322,58.5502),(24.5421,58.5270),(24.5394,58.5119)]}
rb = unary_union([shape(f['geometry']) for f in json.load(open(f'{d}/downloads/plan/rb_planeeringutrass.json'))['features']])
etak = {}
for sub in ('roi01','roi02'):
    for f in json.load(open(f'{d}/downloads/etak/e_501_tee_j_{sub}.json'))['features']:
        p = f['properties']
        if p['tyyp_tekst'] in ('Põhimaantee','Tugimaantee','Kõrvalmaantee'):
            etak.setdefault(f"road {p['tee']} {p['nimetus']}", []).append(shape(f['geometry']))
    for f in json.load(open(f'{d}/downloads/etak/e_502_roobastee_j_{sub}.json'))['features']:
        etak.setdefault('ETAK rail '+str(f['properties']['etak_id']), []).append(shape(f['geometry']))
etak = {k: unary_union(v) for k, v in etak.items()}
extra = {}
for path in sys.argv[2:]:
    fs = json.load(open(path))['features']
    extra[path.split('/')[-1]] = unary_union([shape(f['geometry']) for f in fs])
out = {}
polys = {f['properties']['id']: transform(tr, shape(f['geometry'])) for f in json.load(open(f'{d}/../../inputs/prior_rois.geojson'))['features']}
for rid, pts in C.items():
    line = transform(tr, LineString(pts))
    # refine: project each simplified-line sample onto the ROI core (40 m buffer shrunk by 38 m) to approximate the true centreline
    core = polys[rid].buffer(-38)
    L = line.length
    rows = []
    s = 0.0
    while s <= L:
        pt0 = line.interpolate(s)
        from shapely.ops import nearest_points
        pt = nearest_points(core, pt0)[0]
        near = sorted(((round(g.distance(pt)), k) for k, g in etak.items()))[:3]
        row = {'s_m': round(s), 'lonlat': [round(v,5) for v in Transformer.from_crs(3301,4326,always_xy=True).transform(pt.x, pt.y)], 'in_rb_corridor': rb.contains(pt), 'dist_rb_corridor_m': round(rb.distance(pt)), 'nearest': near}
        for k, g in extra.items(): row['dist_'+k] = round(g.distance(pt))
        rows.append(row); s += 500
    out[rid] = {'simplified_length_m': round(L), 'samples': rows}
    print('==', rid, round(L))
    for r in rows: print(' ', r)
json.dump(out, open(f'{d}/derived_centreline_profile.json','w'), indent=1, ensure_ascii=False)
