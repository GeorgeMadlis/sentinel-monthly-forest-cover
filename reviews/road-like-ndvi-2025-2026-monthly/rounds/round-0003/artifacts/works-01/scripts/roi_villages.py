"""Settlement units (EHAK) traversed by each ROI, with share of ROI area, ordered along the simplified centreline. Usage: python -I roi_villages.py WORKS_DIR"""
import json, sys
from shapely.geometry import shape, LineString
from shapely.ops import transform
from pyproj import Transformer
d = sys.argv[1]
tr = Transformer.from_crs(4326, 3301, always_xy=True).transform
rois = {f['properties']['id']: transform(tr, shape(f['geometry'])) for f in json.load(open(f'{d}/../../inputs/prior_rois.geojson'))['features']}
C = {'ROI-01': [(24.5962,58.4266),(24.6410,58.4629),(24.6928,58.4891),(24.7570,58.5137),(24.8146,58.5426)],
     'ROI-02': [(24.5093,58.5853),(24.5111,58.5669),(24.5322,58.5502),(24.5421,58.5270),(24.5394,58.5119)]}
vs = json.load(open(f'{d}/downloads/ehak/villages.json'))['features']
for rid, poly in rois.items():
    line = transform(tr, LineString(C[rid])) if rid in C else None
    out = []
    for v in vs:
        g = shape(v['geometry']); i = g.intersection(poly)
        if i.area > 10:
            s = line.project(i.centroid) if line else None
            out.append((round(s) if s is not None else None, v['properties']['asustusyksus'], v['properties']['omavalitsus'], round(100*i.area/poly.area, 1)))
    print(rid, sorted(out, key=lambda r: (r[0] or 0)))
