"""Coverage of ROI polygons by cadastral parcel groups (Rail Baltica 'Rapla-Pärnu raudtee', road 4 parcels) and by
Rail Baltica planning corridor, per 500 m bin along the simplified centreline. Usage: python -I parcel_coverage.py WORKS_DIR"""
import json, sys, re
from shapely.geometry import shape, LineString, Polygon
from shapely.ops import transform, unary_union, substring
from pyproj import Transformer
d = sys.argv[1]
tr = Transformer.from_crs(4326, 3301, always_xy=True).transform
rois = {f['properties']['id']: transform(tr, shape(f['geometry'])) for f in json.load(open(f'{d}/../../inputs/prior_rois.geojson'))['features']}
C = {'ROI-01': [(24.5962,58.4266),(24.6410,58.4629),(24.6928,58.4891),(24.7570,58.5137),(24.8146,58.5426)],
     'ROI-02': [(24.5093,58.5853),(24.5111,58.5669),(24.5322,58.5502),(24.5421,58.5270),(24.5394,58.5119)]}
groups = {}
for f in json.load(open(f'{d}/downloads/kataster/linear_parcels.json'))['features']:
    p = f['properties']; a = p['l_aadress']
    if a.startswith('Rapla-Pärnu raudtee'): k = 'RB_parcels_Rapla-Parnu_raudtee'
    elif re.match(r'^4 Tallinna?-Pärnu-Ikla tee', a): k = 'road4_parcels_reg2025_2026' if p['registr'][:4] in ('2025','2026') else 'road4_parcels_reg_pre2025'
    else: continue
    g = shape(f['geometry']); groups.setdefault(k, []).append(g if g.is_valid else g.buffer(0))
groups = {k: unary_union(v) for k, v in groups.items()}
groups['RB_planning_corridor_2018'] = unary_union([shape(f['geometry']) for f in json.load(open(f'{d}/downloads/plan/rb_planeeringutrass.json'))['features']])
out = {}
for rid, poly in rois.items():
    r = {'roi_area_m2': round(poly.area), 'groups': {k: {'overlap_m2': round(poly.intersection(g).area), 'pct_roi_area': round(100*poly.intersection(g).area/poly.area, 1)} for k, g in groups.items()}}
    if rid in C:
        line = transform(tr, LineString(C[rid])); L = line.length; bins = []
        s = 0
        while s < L:
            seg = substring(line, s, min(s+500, L))
            # bin slab: ROI part nearest to this segment (ROI ∩ wide buffer of the segment, flat caps)
            slab = poly.intersection(seg.buffer(600, cap_style=2))
            row = {'from_m': round(s), 'to_m': round(min(s+500, L))}
            for k, g in groups.items():
                row[k] = round(100*slab.intersection(g).area/slab.area) if slab.area > 0 else None
            bins.append(row); s += 500
        r['bins_500m_pct_area'] = bins
    out[rid] = r
json.dump(out, open(f'{d}/derived_parcel_coverage.json', 'w'), indent=1, ensure_ascii=False)
for rid, r in out.items():
    print('==', rid, r['groups'])
    for b in r.get('bins_500m_pct_area', []): print('   ', b)
