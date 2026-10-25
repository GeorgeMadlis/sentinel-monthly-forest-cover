"""Compute sample points (EPSG:3301) along coarse ROI centrelines from addendum geo-01-retask-0001."""
import json
from pyproj import Transformer
from shapely.geometry import LineString
t=Transformer.from_crs(4326,3301,always_xy=True)
lines={'ROI-01':[(24.5962,58.4266),(24.6410,58.4629),(24.6928,58.4891),(24.7570,58.5137),(24.8146,58.5426)],
       'ROI-02':[(24.5093,58.5853),(24.5111,58.5669),(24.5322,58.5502),(24.5421,58.5270),(24.5394,58.5119)]}
fr={'ROI-01':[0.15,0.5,0.85],'ROI-02':[0.25,0.75]}
out={}
for k,v in lines.items():
    L=LineString([t.transform(*p) for p in v])
    for i,f in enumerate(fr[k]):
        p=L.interpolate(f,normalized=True); out[f'{k}-P{i+1}']=(round(p.x),round(p.y))
    print(k,'length m',round(L.length))
for k,p in {'CONTROL-01':(24.6857,58.5777),'CONTROL-02':(24.8071,58.3178)}.items():
    x,y=t.transform(*p); out[k]=(round(x),round(y))
print(json.dumps(out,indent=1))
