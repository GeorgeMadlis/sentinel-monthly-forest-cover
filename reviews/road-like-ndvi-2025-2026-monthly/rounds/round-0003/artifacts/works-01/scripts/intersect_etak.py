"""Intersect ETAK line layers with ROI polygons (EPSG:3301). Usage: python -I intersect_etak.py ROI_GEOJSON ETAK_DIR OUT_JSON"""
import json, sys, collections
from shapely.geometry import shape, mapping
from shapely.ops import transform, unary_union, linemerge
from pyproj import Transformer
roi_path, etak_dir, out = sys.argv[1:4]
tr = Transformer.from_crs(4326, 3301, always_xy=True).transform
rois = {f['properties']['id']: (transform(tr, shape(f['geometry'])), f['properties']) for f in json.load(open(roi_path))['features']}
layers = ['e_501_tee_j', 'e_502_roobastee_j', 'e_503_siht_j', 'e_601_elektriliin_j']
res = {}
for rid, (poly, props) in rois.items():
    L = props.get('length_m')
    r = {'roi_area_m2': round(poly.area), 'roi_length_m': L, 'layers': {}}
    for lay in layers:
        feats = []
        for sub in ('roi01', 'roi02'):
            try:
                feats += json.load(open(f'{etak_dir}/{lay}_{sub}.json'))['features']
            except FileNotFoundError:
                pass
        seen = set(); groups = collections.defaultdict(lambda: {'len_in_m': 0.0, 'n': 0, 'attrs': set(), 'mod': set()})
        for f in feats:
            if f['id'] in seen: continue
            seen.add(f['id'])
            g = shape(f['geometry'])
            inter = g.intersection(poly)
            if inter.is_empty or inter.length < 1: continue
            p = f['properties']
            if lay == 'e_501_tee_j':
                key = f"tee={p.get('tee')}|{p.get('nimetus')}|{p.get('tyyp_tekst')}"
                attr = f"laius={p.get('laius')};kate={p.get('teekate_tekst')}"
            elif lay == 'e_502_roobastee_j':
                key = f"rail etak_id={p.get('etak_id')}|{p.get('tyyp_tekst')}|{p.get('tahtsus_tekst')}"; attr = f"elekter={p.get('elekter_tekst')}"
            elif lay == 'e_601_elektriliin_j':
                key = f"powerline {p.get('nimipinge')}kV"; attr = ''
            else:
                key = 'siht (cutline)'; attr = ''
            gk = groups[key]; gk['len_in_m'] += inter.length; gk['n'] += 1; gk['attrs'].add(attr)
            gk['mod'].add(f"{p.get('muutmisaeg','')[:10]}/geom {p.get('geom_muutmisaeg','')[:10]}")
        rows = []
        for k, v in sorted(groups.items(), key=lambda kv: -kv[1]['len_in_m']):
            rows.append({'feature': k, 'length_inside_roi_m': round(v['len_in_m'], 1),
                         'pct_of_roi_length': round(100 * v['len_in_m'] / L, 1) if L else None,
                         'n_segments': v['n'], 'attrs': sorted(v['attrs']), 'etak_modified(attr/geom)': sorted(v['mod'])[:12]})
        r['layers'][lay] = rows
    res[rid] = r
json.dump(res, open(out, 'w'), indent=1, ensure_ascii=False)
for rid, r in res.items():
    print('==', rid, r['roi_length_m'], r['roi_area_m2'])
    for lay, rows in r['layers'].items():
        for row in rows[:8]:
            print('  ', lay, row['feature'], row['length_inside_roi_m'], row['pct_of_roi_length'], row['n_segments'], row['attrs'][:3], row['etak_modified(attr/geom)'][:4])
