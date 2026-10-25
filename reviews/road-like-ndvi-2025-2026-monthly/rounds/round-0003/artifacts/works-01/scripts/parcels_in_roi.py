"""List cadastral parcels overlapping a ROI. Usage: python -I parcels_in_roi.py ROI_GEOJSON PARCELS_JSON ROI_ID"""
import json, sys
from shapely.geometry import shape
from shapely.ops import transform
from pyproj import Transformer
tr = Transformer.from_crs(4326, 3301, always_xy=True).transform
poly = [transform(tr, shape(f['geometry'])) for f in json.load(open(sys.argv[1]))['features'] if f['properties']['id'] == sys.argv[3]][0]
rows = []
for f in json.load(open(sys.argv[2]))['features']:
    g = shape(f['geometry']); g = g if g.is_valid else g.buffer(0)
    i = g.intersection(poly).area
    if i > 50:
        p = f['properties']; rows.append((round(i), p['tunnus'], p['l_aadress'], p['ay_nimi'], p['ov_nimi'], p['siht1'], p['omvorm'], p['registr'][:10]))
for r in sorted(rows, key=lambda r: -r[0]): print(r)
print('total overlap m2', sum(r[0] for r in rows))
