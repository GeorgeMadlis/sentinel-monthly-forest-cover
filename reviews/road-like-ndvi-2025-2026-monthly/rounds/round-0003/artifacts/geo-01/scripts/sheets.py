"""Query WMS metainfo (GetFeatureInfo, text/plain) every ~1 km along ROI polygons' centreline (approx via polygon skeleton = coarse addendum vertices) to list 1:10000 sheets."""
import json,sys,urllib.request,urllib.parse,re,datetime
from pyproj import Transformer
from shapely.geometry import LineString, shape
t=Transformer.from_crs(4326,3301,always_xy=True)
lines={'ROI-01':[(24.5962,58.4266),(24.6410,58.4629),(24.6928,58.4891),(24.7570,58.5137),(24.8146,58.5426)],
       'ROI-02':[(24.5093,58.5853),(24.5111,58.5669),(24.5322,58.5502),(24.5421,58.5270),(24.5394,58.5119)]}
pts=[]
for k,v in lines.items():
    L=LineString([t.transform(*p) for p in v]); n=int(L.length//1000)+1
    for i in range(n+1):
        p=L.interpolate(i*L.length/n); pts.append((k,i,round(p.x),round(p.y)))
for k,p in {'CONTROL-01':(24.6857,58.5777),'CONTROL-02':(24.8071,58.3178)}.items():
    x,y=t.transform(*p); pts.append((k,0,round(x),round(y)))
res=[]
for k,i,x,y in pts:
    b=f'{y-50},{x-50},{y+50},{x+50}'
    u='https://kaart.maaamet.ee/wms/fotokaart?'+urllib.parse.urlencode({'SERVICE':'WMS','VERSION':'1.3.0','REQUEST':'GetFeatureInfo','LAYERS':'metainfo','QUERY_LAYERS':'metainfo','CRS':'EPSG:3301','BBOX':b,'WIDTH':101,'HEIGHT':101,'I':50,'J':50,'INFO_FORMAT':'text/plain'})
    s=urllib.request.urlopen(u,timeout=60).read().decode('utf-8','replace')
    d=dict(re.findall(r"(\w+): '([^']*)'",s))
    d.update(roi=k,idx=i,x=x,y=y,url=u,retrieved_utc=datetime.datetime.now(datetime.timezone.utc).strftime('%FT%TZ'))
    res.append(d); print(k,i,x,y,d.get('NR_10000'),d.get('LENNUAEG'),d.get('OF_GSD'),d.get('PK_AASTA'))
json.dump(res,open(sys.argv[1],'w'),indent=1)
