from pathlib import Path
import sys,json
from datetime import datetime
import rasterio
import numpy as np
from affine import Affine
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from forest_change.sigma_sar_map import materialize
from forest_change.raster import Grid,read_asset
from forest_change.providers import LocalRasterProvider
from forest_change.algorithms import feature
from forest_change.evidence import write_json,checksum
from rasterio.windows import Window
from pyproj import Transformer
import importlib.util
R=Path(__file__).resolve().parent;REPO=R.parents[1];RUN=REPO/'runs/aoi-s2-s1-jja-2025-2026-sigma';BASE=Path(json.loads((RUN/'maps/map_metadata.json').read_text())['source_run'])
spec=importlib.util.spec_from_file_location('robust',REPO/'.codex/skills/inspect-sentinel-change/scripts/robust_threshold.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
provider=LocalRasterProvider({'inventory':str(RUN/'optical_inventory.json'),'collection':'cached-calibrated'})
ranking=json.loads((BASE/'target_ranking.json').read_text());print([(q['item']['datetime'],q.get('clear_fraction'),q.keys()) for q in ranking[:4]],flush=True)
# Select two highest-ranked clear dates at least ten days from previously selected dates.
selected=[];days=[datetime.fromisoformat('2026-06-20')]
for q in ranking:
 i=q['item'];d=datetime.fromisoformat(i['datetime'][:10]);p=i['properties']
 if not p.get('earthsearch:boa_offset_applied'):continue
 if all(abs((d-old).days)>=10 for old in days):selected.append(i);days.append(d)
 if len(selected)==2:break
ledger=[];tr=Transformer.from_crs(4326,6933,always_xy=True)
points={'ROI-01':(24.7571428571,58.5137213916),'ROI-02':(24.5321428571,58.5502713186)}
for roi,(lon,lat) in points.items():
 x,y=tr.transform(lon,lat);left=np.floor((x-250)/20)*20;top=np.ceil((y+250)/20)*20;grid=Grid('EPSG:6933',Affine(20,0,left,0,-20,top),26,26);win=Window(0,0,26,26)
 def ndvi(item):
  bands={key:read_asset(provider,item['assets'][key],grid,win,categorical=key=='scl') for key in ('red','nir','scl')};v=feature('NDVI',bands);v[~np.isin(bands['scl'],[4,5,6,7])]=np.nan;return v
 refs=np.stack([ndvi(i) for i in provider.items if i['datetime'].startswith('2025')]);dates=[];candidates=[]
 targets=[next(i for i in provider.items if i['datetime'].startswith('2026'))]
 for item in selected:
  try:
   out=R/'cache/persistence'/roi;out.mkdir(parents=True,exist_ok=True)
   mapped=materialize(item,{'red':'red','nir':'nir','scl':'scl'},grid,out);mapped['datetime']=item['datetime'];targets.append(mapped)
  except Exception as ex:ledger.append({'roi_id':roi,'id':item['id'],'status':'inaccessible','error':str(ex)})
 for item in targets:
  values=ndvi(item);res=m.robust_candidate(refs,values);candidate=np.where(res['valid'],res['candidate'],np.nan);candidates.append(candidate)
  folder=R/'experiments/persistence'/roi;folder.mkdir(parents=True,exist_ok=True)
  for label,data in [('NDVI',values),('candidate',candidate)]:
   with rasterio.open(folder/(item['datetime'][:10]+'-'+label+'.tif'),'w',**grid.profile) as dst:dst.write(np.where(np.isfinite(data),data,-9999).astype('float32'),1)
  dates.append({'id':item['id'],'date':item['datetime'],'valid_pixels':int(res['valid'].sum()),'candidate_pixels':int((candidate==1).sum()),'source_independence_group':'Sentinel-2-EarthSearch','assets':item['assets']})
 stack=np.stack(candidates);valid=np.isfinite(stack);enough=(valid.sum(0)>=3);persistent=enough&((stack==1).sum(0)>=2)
 folder=R/'experiments/persistence'/roi
 for label,data in [('valid_date_count',valid.sum(0)),('detection_date_count',(stack==1).sum(0)),('persistent',np.where(enough,persistent,np.nan))]:
  with rasterio.open(folder/(label+'.tif'),'w',**grid.profile) as dst:dst.write(np.where(np.isfinite(data),data,-9999).astype('float32'),1)
 ledger.append({'roi_id':roi,'status':'executed' if len(targets)>=3 else 'partial','dates':dates,'three_date_valid_pixels':int(enough.sum()),'persistent_at_least_two_pixels':int(persistent.sum()),'pixel_ha':grid.pixel_ha,'grid':{'crs':grid.crs,'transform':list(grid.transform),'width':26,'height':26},'limitations':['Same sensor/provider; not independent road labels.','500 m sampling windows only; not corridor-wide persistence.','Summer baseline does not model phenology.'],'selection':'top archived AOI-quality ranking with BOA-offset flag and >=10-day spacing; pixel-level SCL evaluated after acquisition'})
 write_json(R/'persistence_experiment.json',{'records':ledger,'ranking_sha256':checksum(BASE/'target_ranking.json'),'rule':'default robust (k=2.5, delta_min=.15, epsilon=.02, min_ref=5); >=2 detections with >=3 valid target dates'})
print('Persistence processing finished',flush=True)
