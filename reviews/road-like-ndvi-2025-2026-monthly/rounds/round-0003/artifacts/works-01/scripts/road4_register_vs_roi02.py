"""Compare Transpordiamet Teeregister road-4 sections (layer 9) and km points (layer 12) with ROI-02.
Usage: python -I road4_register_vs_roi02.py WORKS_DIR"""
import json, sys
from shapely.geometry import shape, Point, LineString
from shapely.ops import transform, linemerge, unary_union
from pyproj import Transformer
d = sys.argv[1]
tr = Transformer.from_crs(4326, 3301, always_xy=True).transform
inv = Transformer.from_crs(3301, 4326, always_xy=True).transform
roi = [transform(tr, shape(f['geometry'])) for f in json.load(open(f'{d}/../../inputs/prior_rois.geojson'))['features'] if f['properties']['id'] == 'ROI-02'][0]
secs = json.load(open(f'{d}/downloads/teeregister/road4_layer9.geojson'))['features']
kms = sorted((f['properties']['km'], Point(f['geometry']['coordinates'])) for f in json.load(open(f'{d}/downloads/teeregister/road4_layer12.geojson'))['features'])
out = {'sections': [], 'km_points_lonlat': {}, 'bands': {}}
for f in secs:
    p = f['properties']; g = shape(f['geometry'])
    if g.is_empty: continue
    i = g.intersection(roi)
    out['sections'].append({'soidutee': p['soiduteenr'], 'teeosa': p['teeosanr'], 'm_from': p['m_aadress'], 'm_to': p['m_aadress'] + p['pikkus'], 'kasitlus': p['kasit_nimi'], 'suund': p['suund_nimi'], 'modified': p['muudetud_kpv'],
                            'length_in_roi_m': round(i.length), 'min_dist_to_roi_m': round(g.distance(roi))})
for km, pt in kms:
    if 100 <= km <= 118: out['km_points_lonlat'][km] = [round(v, 5) for v in inv(pt.x, pt.y)] + [round(pt.distance(roi))]
# interpolate project km on carriageway-1 km points (linear between consecutive points)
def at_km(k):
    lo = max(x for x in kms if x[0] <= k); hi = min(x for x in kms if x[0] >= k)
    if lo[0] == hi[0]: return lo[1]
    t = (k - lo[0]) / (hi[0] - lo[0]); return Point(lo[1].x + t*(hi[1].x - lo[1].x), lo[1].y + t*(hi[1].y - lo[1].y))
out['project_km'] = {}
for k in (103.5, 108.5, 115.8):
    p = at_km(k); lon, lat = inv(p.x, p.y); out['project_km'][k] = {'lon': round(lon, 5), 'lat': round(lat, 5), 'x': round(p.x), 'y': round(p.y), 'dist_to_roi02_m': round(p.distance(roi))}
# per latitude band: ROI-02 part, distance to carriageway-1 and -2 geometry, nearest km
c1 = unary_union([shape(f['geometry']) for f in secs if f['properties']['soiduteenr'] == 1])
c2 = unary_union([shape(f['geometry']) for f in secs if f['properties']['soiduteenr'] == 2])
from shapely.geometry import box
for name, (a, b) in {'north_58.550-58.585': (58.550, 58.585), 'middle_58.528-58.550': (58.528, 58.550), 'south_58.513-58.528': (58.513, 58.528)}.items():
    x0, y0 = tr(24.4, a); x1, y1 = tr(24.7, b)
    part = roi.intersection(box(min(x0, x1), y0, max(x0, x1), y1))
    ys = []
    nearest_km = sorted(kms, key=lambda kp: kp[1].distance(part))[:2]
    # sample distances from part centreline points to carriageways
    pts = [Point(c) for c in part.exterior.coords] if part.geom_type == 'Polygon' else [Point(c) for g in part.geoms for c in g.exterior.coords]
    dc1 = sorted(round(p.distance(c1)) for p in pts); dc2 = sorted(round(p.distance(c2)) for p in pts)
    out['bands'][name] = {'roi_area_m2': round(part.area), 'carriageway1_len_in_roi_m': round(c1.intersection(part).length), 'carriageway2_len_in_roi_m': round(c2.intersection(part).length),
                          'dist_vertices_to_cw1_m_min_med_max': [dc1[0], dc1[len(dc1)//2], dc1[-1]], 'dist_vertices_to_cw2_m_min_med_max': [dc2[0], dc2[len(dc2)//2], dc2[-1]],
                          'nearest_km_points': [k for k, _ in nearest_km], 'y_range_3301': [round(y0), round(y1)]}
json.dump(out, open(f'{d}/derived_road4_register_vs_roi02.json', 'w'), indent=1)
print(json.dumps(out, indent=1)[:6000])
