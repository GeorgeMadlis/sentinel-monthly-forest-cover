"""ROI-01-S0: overlay ROI on 2023/2024/2025 orthophoto windows and build a 3-panel composite (1500 px wide)."""
import sys,json
from PIL import Image,ImageDraw
from pyproj import Transformer
from shapely.geometry import shape
from shapely.ops import transform
rois,site,cx,cy,half,raw,out=sys.argv[1],sys.argv[2],*map(float,sys.argv[3:6]),sys.argv[6],sys.argv[7]
x0,y0,x1,y1=cx-half,cy-half,cx+half,cy+half
tr=Transformer.from_crs(4326,3301,always_xy=True).transform
geoms=[transform(tr,shape(f['geometry'])) for f in json.load(open(rois))['features']]
layers=[('of2023mets','flight-2023-06-09'),('of2024asulad','flight-2024-05-03'),('of2025aero','flight-2025-04-03')]
tiles=[]
for L,lab in layers:
    im=Image.open(f'{raw}/{site}_{L}.jpg').convert('RGB'); W,H=im.size; d=ImageDraw.Draw(im)
    for g in geoms:
        for p in ([g] if g.geom_type=='Polygon' else g.geoms):
            d.line([((x-x0)/(x1-x0)*W,(y1-y)/(y1-y0)*H) for x,y in p.exterior.coords],fill=(255,0,255),width=2)
    s=100/(2*half)*W; d.rectangle([10,H-22,10+s,H-16],fill=(255,255,0)); d.text((12,H-36),'100 m',fill=(255,255,0))
    d.rectangle([0,0,W,16],fill=(0,0,0)); d.text((3,2),f'{site} {L} {lab}; EPSG:3301 centre {cx:.0f},{cy:.0f}; (c) Maa- ja Ruumiamet, retrieved 2026-10-24',fill=(255,255,0))
    im.save(f'{out}/{site}_{L}_{lab}.png'); tiles.append(im)
c=Image.new('RGB',(1500,500),'white')
for i,t in enumerate(tiles): c.paste(t.resize((500,500)),(i*500,0))
c.save(f'{out}/{site}_composite_2023-2024-2025.png')
