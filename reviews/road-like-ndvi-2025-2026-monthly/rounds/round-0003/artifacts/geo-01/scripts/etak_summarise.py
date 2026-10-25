"""Summarise ETAK features intersecting ROI polygons from saved WFS JSON (no network)."""
import sys,json,pathlib
from pyproj import Transformer
from shapely.geometry import shape
from shapely.ops import transform
rois=json.load(open(sys.argv[1])); d=pathlib.Path(sys.argv[2])
tr=Transformer.from_crs(4326,3301,always_xy=True).transform
keep=['etak_id','kood_tekst','tyyp_tekst','laius','teekate_tekst','tee','nimetus','tahtsus_tekst','muutmisaeg','geom_muutmisaeg','andmeallika_id','ruumikujuallika_id']
rows=[]
for f in rois['features']:
    rid=f['properties']['id']; g=transform(tr,shape(f['geometry']))
    for p in sorted(d.glob(f'{rid}_e_*.json')):
        lyr=p.stem.split(rid+'_')[1]
        for ft in json.loads(p.read_bytes()).get('features',[]):
            fg=shape(ft['geometry']); i=fg.intersection(g)
            if i.is_empty: continue
            line=fg.geom_type.endswith('LineString')
            rows.append(dict(roi=rid,layer=lyr,in_roi=round(i.length if line else i.area,1),unit='m' if line else 'm2',total=round(fg.length if line else fg.area,1),**{k:ft['properties'].get(k) for k in keep}))
rows.sort(key=lambda r:(r['roi'],-r['in_roi']))
json.dump(rows,open(d/'etak_in_roi_summary.json','w'),indent=1,ensure_ascii=False)
for r in rows:
    if r['in_roi']>=100 or r['layer'] in ('e_502_roobastee_j','e_503_siht_j','e_601_elektriliin_j','e_501_tee_a'):
        print(r['roi'],r['layer'],r['in_roi'],r['unit'],'/',r['total'],'|',r['tyyp_tekst'],r['teekate_tekst'],'laius=',r['laius'],'tee=',r['tee'],r['nimetus'],'| muut',r['muutmisaeg'],'geom',r['geom_muutmisaeg'])
import collections
print('max muutmisaeg per roi:',{k:max((r['muutmisaeg'] or '') for r in rows if r['roi']==k) for k in set(r['roi'] for r in rows)})
print('features with geom change >= 2025-01-01:',[(r['roi'],r['layer'],r['etak_id'],r['in_roi'],r['geom_muutmisaeg']) for r in rows if (r['geom_muutmisaeg'] or '')>='2025'])
