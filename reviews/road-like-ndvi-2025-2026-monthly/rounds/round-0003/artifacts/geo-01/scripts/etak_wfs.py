"""Fetch ETAK line layers (WFS 2.0, JSON, EPSG:3301) for each ROI bbox and summarise features intersecting the ROI polygon.
usage: etak_wfs.py ROIS OUTDIR"""
import sys,json,hashlib,datetime,urllib.request,urllib.parse,pathlib
from pyproj import Transformer
from shapely.geometry import shape
from shapely.ops import transform
rois=json.load(open(sys.argv[1])); out=pathlib.Path(sys.argv[2]); out.mkdir(exist_ok=True,parents=True)
tr=Transformer.from_crs(4326,3301,always_xy=True).transform
log=[];summ=[]
for f in rois['features']:
    rid=f['properties']['id']; g=transform(tr,shape(f['geometry'])); b=g.bounds
    for lyr in ['e_501_tee_j','e_502_roobastee_j','e_503_siht_j','e_601_elektriliin_j','e_501_tee_a']:
        p={'service':'WFS','version':'2.0.0','request':'GetFeature','typeNames':'etak:'+lyr,'outputFormat':'application/json','srsName':'EPSG:3301',
           'bbox':f'{b[0]-100:.0f},{b[1]-100:.0f},{b[2]+100:.0f},{b[3]+100:.0f},EPSG:3301','count':5000}
        u='https://gsavalik.envir.ee/geoserver/etak/wfs?'+urllib.parse.urlencode(p)
        ts=datetime.datetime.now(datetime.timezone.utc).strftime('%FT%TZ')
        data=urllib.request.urlopen(u,timeout=120).read()
        fn=out/f'{rid}_{lyr}.json'; fn.write_bytes(data)
        try: fc=json.loads(data)
        except Exception as e: print(rid,lyr,'nonjson',data[:200]); continue
        # bbox may be interpreted with axis order; check coordinate sanity
        feats=fc.get('features',[])
        log.append({'roi':rid,'layer':lyr,'url':u,'retrieved_utc':ts,'sha256':hashlib.sha256(data).hexdigest(),'file':str(fn),'n_features_bbox':len(feats)})
        for ft in feats:
            try: fg=shape(ft['geometry'])
            except Exception: continue
            inter=fg.intersection(g)
            if inter.is_empty: continue
            L=inter.length if fg.geom_type.endswith('LineString') else inter.area
            tot=fg.length if fg.geom_type.endswith('LineString') else fg.area
            pr=ft['properties']
            summ.append({'roi':rid,'layer':lyr,'id':ft.get('id'),'in_roi_m_or_m2':round(L,1),'feature_total':round(tot,1),
              'frac_inside':round(L/tot,3) if tot else None,
              'props':{k:v for k,v in pr.items() if k.lower() in ('etak_id','tyyp','tyyp_tekst','teekate','teekate_tekst','tee_nr','nimetus','laius','kood','olek','olek_tekst','muudetud','alguskuupaev','moodustatud','tekkimise_kp','muutmise_kp','etak_moodustamise_kp','kood_tekst','tahtsus','nimi','tee_kategooria')}})
        print(rid,lyr,len(feats),'bbox feats; in ROI:',sum(1 for s in summ if s['roi']==rid and s['layer']==lyr))
json.dump(log,open(out/'etak_fetch_log.json','w'),indent=1); json.dump(summ,open(out/'etak_in_roi_summary.json','w'),indent=1,ensure_ascii=False)
# print property keys once
for p in out.glob('*_e_501_tee_j.json'):
    fc=json.loads(p.read_bytes()); 
    if fc.get('features'): print('keys',list(fc['features'][0]['properties'].keys())); break
