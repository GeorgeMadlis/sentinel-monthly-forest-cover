from pathlib import Path
from datetime import datetime,timezone
import sys,json
import requests,rasterio
from rasterio.transform import from_bounds
from pyproj import Transformer
from PIL import Image
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from forest_change.evidence import checksum,write_json
R=Path(__file__).resolve().parent;cache=R/'cache/orthophotos';cache.mkdir(parents=True,exist_ok=True)
u='https://kaart.maaamet.ee/wms/ajalooline';fwd=Transformer.from_crs(4326,3857,always_xy=True);inv=Transformer.from_crs(3857,4326,always_xy=True);est=Transformer.from_crs(4326,3301,always_xy=True)
x0,y0=fwd.transform(24.4,58.2);x1,y1=fwd.transform(24.9,58.6)
ledger=[]
for roi,px,py in [('ROI-01',1000,463),('ROI-02',370,267)]:
 lon,lat=inv.transform(x0+px/1400*(x1-x0),y1-py/2137*(y1-y0));x,y=est.transform(lon,lat);bbox=[x-250,y-250,x+250,y+250]
 for year in (2024,2025):
  layer=f'of{year}aero';params={'service':'WMS','version':'1.1.1','request':'GetMap','layers':layer,'styles':'','srs':'EPSG:3301','bbox':','.join(map(str,bbox)),'width':1000,'height':1000,'format':'image/png','transparent':'TRUE'}
  name=f'{roi}-{year}';p=cache/(name+'.png');record={'id':name,'roi_id':roi,'source_url':u,'query':params,'retrieved_at':datetime.now(timezone.utc).isoformat(),'layer_year':year,'observation_date':None,'source_independence_group':'national-aerial-imagery','display_resolution_m':.5,'native_resolution':'not yet established; requested WMS sampling is not native resolution','bbox_epsg3301':bbox,'point_wgs84':[lon,lat],'limitations':['Layer year is not exact acquisition date; WMS rendering is derived, not a native source tile.']}
  try:
   response=requests.get(u,params=params,timeout=35);response.raise_for_status();p.write_bytes(response.content);im=Image.open(p).convert('RGBA');a=np.array(im);record['nontransparent_fraction']=float((a[:,:,3]>0).mean());record['sha256']=checksum(p);record['path']=str(p.relative_to(R))
   if (a[:,:,3]>0).any():
    tif=cache/(name+'.tif');profile={'driver':'GTiff','width':1000,'height':1000,'count':4,'dtype':'uint8','crs':'EPSG:3301','transform':from_bounds(*bbox,1000,1000),'tiled':True,'compress':'deflate'}
    with rasterio.open(tif,'w',**profile) as dst:dst.write(a.transpose(2,0,1))
    record['georeferenced_path']=str(tif.relative_to(R));record['tif_sha256']=checksum(tif)
   info={**params,'request':'GetFeatureInfo','query_layers':'metainfo','layers':'metainfo','info_format':'text/plain','x':500,'y':500,'feature_count':10}
   resp=requests.get(u,params=info,timeout=25);resp.raise_for_status();ip=cache/(name+'-metadata.txt');ip.write_bytes(resp.content);record['metadata_path']=str(ip.relative_to(R));record['metadata_query']=info
   record['accessibility']='available' if record['nontransparent_fraction']>.01 else 'no coverage'
  except Exception as ex:record['accessibility']='inaccessible';record['error']=str(ex)
  ledger.append(record);write_json(R/'independent_map_evidence.json',{'records':ledger,'license':'Official open data; attribute Republic of Estonia Land and Spatial Development Board and retrieval date.','source_reference':'https://geoportaal.maaruum.ee/eng/spatial-data/orthophotos/download-orthophotos-p662.html'})
print(json.dumps(ledger,indent=2))
