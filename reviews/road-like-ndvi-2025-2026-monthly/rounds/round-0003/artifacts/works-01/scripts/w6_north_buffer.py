"""W6: forest notices (valid + archived RD/LR) and road-4 parcels within 200 m of ROI-02 north stretch (58.550-58.585 N);
also EHAK Kangru/Parisselja boundary crossing of road 4. Usage: python -I w6_north_buffer.py WORKS_DIR"""
import json, sys, re
from shapely.geometry import shape, box
from shapely.ops import transform, unary_union
from pyproj import Transformer
d = sys.argv[1]
tr = Transformer.from_crs(4326, 3301, always_xy=True).transform
inv = Transformer.from_crs(3301, 4326, always_xy=True).transform
roi = [transform(tr, shape(f['geometry'])) for f in json.load(open(f'{d}/../../inputs/prior_rois.geojson'))['features'] if f['properties']['id'] == 'ROI-02'][0]
x0, y0 = tr(24.4, 58.550); x1, y1 = tr(24.7, 58.585)
north = roi.intersection(box(min(x0, x1), y0, max(x0, x1), y1)); zone = north.buffer(200)
road4 = unary_union([shape(f['geometry']) for f in json.load(open(f'{d}/downloads/teeregister/road4_layer9.geojson'))['features'] if f['properties']['soiduteenr'] == 1])
print('north part area', round(north.area), 'zone area', round(zone.area), 'road4 length in zone', round(road4.intersection(zone).length))
res = {'notices': [], 'parcels': []}
for path in ('metsaregister/teatis_roi02.json', 'metsaregister/teatis_arhiiv_RD_LR_roi02.json'):
    for f in json.load(open(f'{d}/downloads/{path}'))['features']:
        g = shape(f['geometry']); g = g if g.is_valid else g.buffer(0); p = f['properties']
        a = g.intersection(zone).area
        if a > 1:
            res['notices'].append({'src': path.split('/')[-1], 'teatise_nr': p['teatise_nr'], 'too_kood': p['too_kood'], 'otsus': p['otsus'], 'approved': (p['otsus_kinnitatud_kp'] or '')[:10], 'katastri_nr': p['katastri_nr'],
                                   'area_in_zone_m2': round(a), 'area_in_roi_north_m2': round(g.intersection(north).area), 'dist_to_road4_m': round(g.distance(road4)), 'lat': round(inv(g.centroid.x, g.centroid.y)[1], 4)})
for f in json.load(open(f'{d}/downloads/kataster/linear_parcels.json'))['features']:
    p = f['properties']
    if not re.match(r'^4 Tallinna?-Pärnu-Ikla tee', p['l_aadress']): continue
    g = shape(f['geometry']); g = g if g.is_valid else g.buffer(0); a = g.intersection(zone).area
    if a > 1:
        res['parcels'].append({'tunnus': p['tunnus'], 'l_aadress': p['l_aadress'], 'ay_nimi': p['ay_nimi'], 'registr': p['registr'][:10], 'siht1': p['siht1'], 'omvorm': p['omvorm'],
                               'area_in_zone_m2': round(a), 'area_in_roi_north_m2': round(g.intersection(north).area), 'lat': round(inv(g.centroid.x, g.centroid.y)[1], 4)})
vs = {v['properties']['asustusyksus']: shape(v['geometry']) for v in json.load(open(f'{d}/downloads/ehak/villages.json'))['features']}
b = vs['Kangru küla'].boundary.intersection(vs['Parisselja küla'].boundary)
x = road4.intersection(b)
res['kangru_parisselja_boundary_x_road4'] = [[round(v, 5) for v in inv(p.x, p.y)] for p in getattr(x, 'geoms', [x]) if not p.is_empty and p.geom_type == 'Point']
xr = roi.intersection(b)
res['kangru_parisselja_boundary_x_roi02_lat'] = round(inv(xr.centroid.x, xr.centroid.y)[1], 4) if not xr.is_empty else None
res['notices'].sort(key=lambda r: r['approved']); res['parcels'].sort(key=lambda r: r['registr'])
json.dump(res, open(f'{d}/derived_w6_north_buffer.json', 'w'), indent=1, ensure_ascii=False)
for k in ('notices', 'parcels'):
    print('==', k, len(res[k]))
    for r in res[k]: print('  ', r)
print(res['kangru_parisselja_boundary_x_road4'], res['kangru_parisselja_boundary_x_roi02_lat'])
