from pathlib import Path
import sys,importlib.util,json,csv,shutil
from contextlib import ExitStack
import numpy as np,rasterio
from pyproj import Transformer
from shapely.geometry import LineString,box,mapping
from rasterio.features import geometry_mask
from rasterio.warp import transform_geom
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from forest_change.providers import LocalRasterProvider
from forest_change.raster import Grid,tiles,read_asset,write_window
from forest_change.algorithms import feature,fuse
from forest_change.evidence import checksum,write_json
from forest_change.leaflet import visual_grid,anomaly_rgba,generate_map
from PIL import Image
R=Path(__file__).resolve().parent;REPO=R.parents[1];RUN=REPO/'runs/aoi-s2-s1-jja-2025-2026-sigma';E=R/'experiments';E.mkdir(exist_ok=True)
spec=importlib.util.spec_from_file_location('robust',REPO/'.codex/skills/inspect-sentinel-change/scripts/robust_threshold.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);mod.self_test()
provider=LocalRasterProvider({'inventory':str(RUN/'optical_inventory.json'),'collection':'archived-calibrated-s2'})
ref=[i for i in provider.items if i['datetime'].startswith('2025')];target=next(i for i in provider.items if i['datetime'].startswith('2026'));assert len({i['datetime'][:10] for i in ref})==8
with rasterio.open(RUN/'w0000/NDVI_current.tif') as s:grid=Grid(str(s.crs),s.transform,s.width,s.height)
fwd=Transformer.from_crs(4326,3857,always_xy=True);proj=Transformer.from_crs(3857,6933,always_xy=True)
x0,y0=fwd.transform(24.4,58.2);x1,y1=fwd.transform(24.9,58.6)
def displaypoint(x,y):return proj.transform(x0+x/1400*(x1-x0),y1-y/2137*(y1-y0))
lines={'ROI-01':[(550,927),(675,735),(820,595),(1000,463),(1160,310)],'ROI-02':[(306,82),(311,178),(370,267),(398,392),(390,470)]}
regions={};features=[]
for name,points in lines.items():
 line=LineString([displaypoint(x,y) for x,y in points]);poly=line.buffer(40)
 regions[name]=mapping(poly)
 features.append({'type':'Feature','properties':{'id':name,'role':'candidate-corridor','length_m':round(line.length,1),'buffer_m':40,'apparent_width_m':'approximately 20–60, visual and unresolved edges','source_pixel_width':'approximately 2–6 at 10 m; not independently measured','analysis_pixel_width':'approximately 1–3 at 20 m','uncertainty':'manual coarse centreline; 40 m sampling buffer is declared tolerance, not measured registration error'},'geometry':transform_geom(grid.crs,'EPSG:4326',mapping(poly))})
# Comparison controls: visual forest background patches. Not independently labeled unchanged.
for name,xy in {'CONTROL-01':(800,120),'CONTROL-02':(1140,1510)}.items():
 x,y=displaypoint(*xy);p=box(x-160,y-160,x+160,y+160);regions[name]=mapping(p)
 features.append({'type':'Feature','properties':{'id':name,'role':'visual-control','uncertainty':'stable-looking forest; no independent stability label'},'geometry':transform_geom(grid.crs,'EPSG:4326',mapping(p))})
write_json(R/'rois.geojson',{'type':'FeatureCollection','features':features})
settings=[(k,d,e) for k in (2,2.5,3) for d in (.1,.15,.2) for e in (.02,.05)]
results={p:{'valid':0,'paired_valid':0,'optical':0,'and':0,'or':0,'discordant':0,'shared_all_baselines_valid':0,'shared_optical':0} for p in settings}
samples={n:{k:[] for k in ('ndvi_change','vv_change','vh_change','count','std')} for n in regions};roi_counts={n:{'valid':0,'fixed':0,'sigma':0,'sar':0,'fixed_and':0,'sigma_and':0,'vv_only_fail':0,'vh_only_fail':0,'both_fail':0} for n in regions}
with ExitStack() as stack:
 src={k:stack.enter_context(rasterio.open(RUN/'w0000'/p)) for k,p in {'current':'NDVI_current.tif','change':'NDVI_change.tif','mean':'NDVI_reference.tif','std':'NDVI_reference_std.tif','count':'NDVI_reference_count.tif','vv':'VV_change.tif','vh':'VH_change.tif','sigma':'optical_candidate.tif','sar':'sar_candidate.tif'}.items()}
 base=Path(json.loads((RUN/'maps/map_metadata.json').read_text())['source_run']);src['fixed']=stack.enter_context(rasterio.open(base/'w0000/disturbance.tif'))
 dst={}
 for setting in settings:
  k,d,e=setting;name=f'k{k:g}_drop{d:g}_floor{e:g}';folder=E/name;folder.mkdir(exist_ok=True)
  dst[setting]={mode:stack.enter_context(rasterio.open(folder/f'{mode}.tif','w',**grid.profile)) for mode in ('optical','and','or','discordance')}
 default=(2.5,.15,.02)
 diagnostic={key:stack.enter_context(rasterio.open(E/f'robust_{key}.tif','w',**grid.profile)) for key in ('median','mad','score','count')}
 for w in tiles(grid,512):
  a={k:s.read(1,window=w,masked=True).filled(np.nan) for k,s in src.items()}
  ndvis=[]
  for item in ref:
   bands={key:read_asset(provider,item['assets'][key],grid,w,categorical=key=='scl') for key in ('red','nir','scl')}
   ndvi=feature('NDVI',bands);ndvi[~np.isin(bands['scl'],[4,5,6,7])]=np.nan;ndvis.append(ndvi)
  refs=np.stack(ndvis)
  # Archived reference composition reproduces exactly within floating point tolerance.
  import warnings
  with warnings.catch_warnings():
   warnings.simplefilter('ignore',RuntimeWarning);means=np.nanmean(refs,axis=0);std=np.nanstd(refs,axis=0)
  v=np.isfinite(a['mean']);assert np.allclose(means[v],a['mean'][v],atol=2e-6)
  sv=np.isfinite(a['std']);assert np.allclose(std[sv],a['std'][sv],atol=2e-6)
  for setting in settings:
   k,d,e=setting;r=mod.robust_candidate(refs,a['current'],k=k,delta_min=d,epsilon=e,min_count=5)
   optical=np.where(r['valid'],r['candidate'],np.nan).astype('float32');both=np.isfinite(optical)&np.isfinite(a['sar']);shared=both&np.isfinite(a['fixed'])&np.isfinite(a['sigma'])
   and_mask,_,discord=fuse(optical,a['sar'],'optical_and_sar');or_mask,_,_=fuse(optical,a['sar'],'optical_or_sar')
   masks={'optical':optical,'and':and_mask,'or':or_mask,'discordance':discord}
   out=results[setting]
   for key,value in {'valid':r['valid'].sum(),'paired_valid':both.sum(),'optical':(optical==1).sum(),'and':(and_mask==1).sum(),'or':(or_mask==1).sum(),'discordant':(discord==1).sum(),'shared_all_baselines_valid':shared.sum(),'shared_optical':((optical==1)&shared).sum()}.items():out[key]+=int(value)
   for mode,values in masks.items():write_window(dst[setting][mode],values,w)
   if setting==default:
    for key in diagnostic:write_window(diagnostic[key],r[key].astype('float32'),w)
  for name,geom in regions.items():
   gate=geometry_mask([geom],out_shape=a['current'].shape,transform=rasterio.windows.transform(w,grid.transform),invert=True)
   valid=gate&np.isfinite(a['fixed'])&np.isfinite(a['sigma'])&np.isfinite(a['sar']);c=roi_counts[name];c['valid']+=int(valid.sum())
   for key in ('fixed','sigma','sar'):c[key]+=int(((a[key]==1)&valid).sum())
   for key in ('fixed','sigma'):c[key+'_and']+=int(((a[key]==1)&(a['sar']==1)&valid).sum())
   rejection=valid&(a['sigma']==1)&(a['sar']==0);vf=a['vv']>=-1.5;hf=a['vh']>=-1
   for key,m in {'vv_only_fail':vf&~hf,'vh_only_fail':hf&~vf,'both_fail':vf&hf}.items():c[key]+=int((m&rejection).sum())
   for key,arr in {'ndvi_change':a['change'],'vv_change':a['vv'],'vh_change':a['vh'],'count':a['count'],'std':a['std']}.items():samples[name][key].extend(arr[gate&np.isfinite(arr)].tolist())
records=[]
for setting,c in results.items():
 k,d,e=setting;folder=E/f'k{k:g}_drop{d:g}_floor{e:g}';records.append({'k':k,'delta_min':d,'epsilon':e,**c,'candidate_ha':c['optical']*grid.pixel_ha,'and_ha':c['and']*grid.pixel_ha,'artifacts':{p.name:{'path':str(p.relative_to(R)),'sha256':checksum(p)} for p in folder.glob('*.tif')}})
write_json(R/'threshold_experiments.json',{'status':'executed','helper_sha256':checksum(REPO/'.codex/skills/inspect-sentinel-change/scripts/robust_threshold.py'),'self_test':'5 synthetic checks passed','reference_item_ids':[i['id'] for i in ref],'reference_unique_dates':8,'target':target['id'],'min_count':5,'settings':records,'baseline_reproduction':'reference mean/std reproduced tile by tile within 2e-6','interpretation':'heuristic, no independent labels or probability calibration'})
rows=[]
for name,data in samples.items():
 row={'roi_id':name,**roi_counts[name]}
 for key,values in data.items():
  row[key+'_n']=len(values)
  for label,q in [('p10',.1),('median',.5),('p90',.9)]:row[key+'_'+label]=float(np.quantile(values,q)) if values else None
 rows.append(row)
with (R/'roi_metrics.csv').open('w') as f:writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
write_json(R/'roi_metrics.json',rows)
# All settings have a common display grid, original backgrounds, vendored Leaflet and masks.
aoi={'type':'Polygon','coordinates':[[[24.4,58.2],[24.9,58.2],[24.9,58.6],[24.4,58.6],[24.4,58.2]]]};vg=visual_grid(aoi)
from rasterio.windows import Window
vw=Window(0,0,vg.width,vg.height)
selected={'reference':{'item':ref[0]},'target':{'item':target}}
for record in records:
 folder=R/record['artifacts']['optical.tif']['path'];folder=folder.parent
 for mode in ('optical','and','or'):
  maps=folder/('maps_'+mode);maps.mkdir(exist_ok=True)
  values=read_asset(provider,{'href':str(folder/f'{mode}.tif'),'scale':1,'offset':0},vg,vw,categorical=True);Image.fromarray(anomaly_rgba(values)).save(maps/'anomalies.png')
  for role in ('reference','target'):shutil.copyfile(R/f'{role}.png',maps/f'{role}.png')
  for asset in ('leaflet.js','leaflet.css'):shutil.copyfile(RUN/'maps'/asset,maps/asset)
  shutil.copytree(RUN/'maps/images',maps/'images',dirs_exist_ok=True)
  generate_map(maps/'map.html',aoi,[[58.2,24.4],[58.6,24.9]],selected,{'run_id':'review-experiment','method':f'Robust NDVI {mode}','threshold':{k:record[k] for k in ('k','delta_min','epsilon')},'legend':'Red: experimental candidate; transparent: negative or unavailable; not road identity','reference_note':'RGB reference is 15 June; robust median uses eight dates','heuristic':True})
print(json.dumps({'settings':len(records),'default':next(r for r in records if (r['k'],r['delta_min'],r['epsilon'])==default),'roi_metrics':rows},indent=2))
