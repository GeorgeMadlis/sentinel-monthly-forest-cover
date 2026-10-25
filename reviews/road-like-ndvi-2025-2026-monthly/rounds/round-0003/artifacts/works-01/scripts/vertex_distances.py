"""Distances from ROI polygon vertices to selected ETAK national roads / rail. Usage: python -I vertex_distances.py WORKS_DIR ROI_ID"""
import json, sys
from shapely.geometry import shape, Point
from shapely.ops import transform, unary_union
from pyproj import Transformer
d, rid = sys.argv[1:3]
tr = Transformer.from_crs(4326, 3301, always_xy=True).transform
f = [f for f in json.load(open(f'{d}/../../inputs/prior_rois.geojson'))['features'] if f['properties']['id'] == rid][0]
poly = transform(tr, shape(f['geometry']))
L = {}
for sub in ('roi01','roi02'):
    for g in json.load(open(f'{d}/downloads/etak/e_501_tee_j_{sub}.json'))['features']:
        p = g['properties']
        if p['tee'] in (4, 5, 59, 19203, 19219): L.setdefault(f"road{p['tee']}", []).append(shape(g['geometry']))
    for g in json.load(open(f'{d}/downloads/etak/e_502_roobastee_j_{sub}.json'))['features']:
        L.setdefault('rail', []).append(shape(g['geometry']))
L = {k: unary_union(v) for k, v in L.items()}
rb = unary_union([shape(g['geometry']) for g in json.load(open(f'{d}/downloads/plan/rb_planeeringutrass.json'))['features']])
print(rid, 'bounds3301', [round(v) for v in poly.bounds], 'dist poly->', {k: round(poly.distance(v)) for k, v in L.items()}, 'rb', round(poly.distance(rb)))
inv = Transformer.from_crs(3301, 4326, always_xy=True).transform
coords = list(poly.exterior.coords)
for c in coords[::max(1, len(coords)//25)]:
    pt = Point(c); lo, la = inv(*c)
    print(f'{lo:.5f},{la:.5f}', {k: round(pt.distance(v)) for k, v in L.items()}, 'rb', round(pt.distance(rb)))
