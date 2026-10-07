from pathlib import Path
import sys,json
from contextlib import ExitStack
import numpy as np,rasterio
from rasterio.features import geometry_mask
from rasterio.warp import transform_geom
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from forest_change.evidence import write_json
R=Path(__file__).parent;RUN=R.parents[1]/'runs/aoi-s2-s1-jja-2025-2026-sigma';base=Path(json.loads((RUN/'maps/map_metadata.json').read_text())['source_run'])
rois=json.loads((R/'rois.geojson').read_text())['features'];results={r['properties']['id']:{'counts':dict.fromkeys(['joint_valid','both','optical_only','radar_only','neither','optical_valid_radar_unavailable'],0),'sigma_rejected_vv':[],'sigma_rejected_vh':[]} for r in rois};shared_counts=dict.fromkeys(['valid','fixed','fixed_sar','sigma','sigma_sar','robust','robust_sar'],0)
with ExitStack() as stack:
 paths={'fixed':base/'w0000/disturbance.tif','sigma':RUN/'w0000/optical_candidate.tif','sar':RUN/'w0000/sar_candidate.tif','vv':RUN/'w0000/VV_change.tif','vh':RUN/'w0000/VH_change.tif','robust':R/'experiments/k2.5_drop0.15_floor0.02/optical.tif'}
 src={k:stack.enter_context(rasterio.open(p)) for k,p in paths.items()};first=src['robust'];geoms={r['properties']['id']:transform_geom('EPSG:4326',first.crs,r['geometry']) for r in rois}
 for _,w in first.block_windows(1):
  a={k:s.read(1,window=w,masked=True).filled(np.nan) for k,s in src.items()};shared=np.isfinite(a['fixed'])&np.isfinite(a['sigma'])&np.isfinite(a['sar'])&np.isfinite(a['robust']);shared_counts['valid']+=int(shared.sum())
  for k in ('fixed','sigma','robust'):
   shared_counts[k]+=int((shared&(a[k]==1)).sum());shared_counts[k+'_sar']+=int((shared&(a[k]==1)&(a['sar']==1)).sum())
  for roi,geom in geoms.items():
   gate=geometry_mask([geom],out_shape=a['robust'].shape,transform=rasterio.windows.transform(w,first.transform),invert=True);v=gate&np.isfinite(a['robust'])&np.isfinite(a['sar']);c=results[roi]['counts'];o=a['robust']==1;s=a['sar']==1
   for k,m in {'joint_valid':v,'both':v&o&s,'optical_only':v&o&~s,'radar_only':v&~o&s,'neither':v&~o&~s,'optical_valid_radar_unavailable':gate&np.isfinite(a['robust'])&~np.isfinite(a['sar'])}.items():c[k]+=int(m.sum())
   rej=gate&(a['sigma']==1)&(a['sar']==0)
   for key in ('vv','vh'):results[roi]['sigma_rejected_'+key].extend(a[key][rej].tolist())
for r in results.values():
 for key in ('vv','vh'):
  arr=r.pop('sigma_rejected_'+key);r['sigma_rejected_'+key+'_summary']={'n':len(arr),'p10_median_p90':np.quantile(arr,[.1,.5,.9]).tolist() if arr else None}
write_json(R/'common_support_and_roi_robust.json',{'default_robust_shared_support':shared_counts,'roi_robust_categories':results,'scope':'provisional manually sampled corridor buffers and visual controls; all areas use .04 ha/pixel'})
print(json.dumps(shared_counts))
