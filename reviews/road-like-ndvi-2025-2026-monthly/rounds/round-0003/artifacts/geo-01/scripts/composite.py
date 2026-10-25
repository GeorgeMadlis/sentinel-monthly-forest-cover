"""Overlay ROI outline on each site window and build a side-by-side composite (<=1500 px wide).
usage: composite.py ROIS SITE CX CY HALF RAWDIR OUTDIR"""
import sys,json
from PIL import Image,ImageDraw
from pyproj import Transformer
from shapely.geometry import shape
from shapely.ops import transform
rois,site,cx,cy,half,raw,out=sys.argv[1],sys.argv[2],*map(float,sys.argv[3:6]),sys.argv[6],sys.argv[7]
x0,y0,x1,y1=cx-half,cy-half,cx+half,cy+half
tr=Transformer.from_crs(4326,3301,always_xy=True).transform
geoms=[transform(tr,shape(f['geometry'])) for f in json.load(open(rois))['features']]
layers=[('of2023mets','jpg','RGB ortho flight 2023-06-09 (of2023mets)'),('of2025aero','jpg','RGB ortho flight 2025-04-03 (of2025aero)'),('pk_vr2024','png','Basic map pk_vr2024 edition'),('pk_vr2026','png','Basic map pk_vr2026 edition')]
tiles=[]
for L,ext,cap in layers:
    im=Image.open(f'{raw}/{site}_{L}.{ext}').convert('RGB'); W,H=im.size; d=ImageDraw.Draw(im)
    for g in geoms:
        for p in ([g] if g.geom_type=='Polygon' else g.geoms):
            d.line([((x-x0)/(x1-x0)*W,(y1-y)/(y1-y0)*H) for x,y in p.exterior.coords],fill=(255,0,255),width=2)
    # 100 m scale bar
    s=100/(2*half)*W; d.rectangle([10,H-22,10+s,H-16],fill=(255,255,0)); d.text((12,H-36),'100 m',fill=(255,255,0))
    d.rectangle([0,0,W,16],fill=(0,0,0)); d.text((3,2),f'{site} {cap}; EPSG:3301 centre {cx:.0f},{cy:.0f}; (c) Maa- ja Ruumiamet, retrieved 2026-10-24',fill=(255,255,0))
    fn=f'{out}/{site}_{L}_{"flight-2023-06-09" if L=="of2023mets" else "flight-2025-04-03" if L=="of2025aero" else "map-edition-"+L[-4:]}.png'
    im.save(fn); tiles.append(im); print(fn)
c=Image.new('RGB',(1500,750),'white')
for i,t in enumerate(tiles):
    c.paste(t.resize((750,750)) if False else t.resize((375*2//2*1,375)) ,(0,0)) if False else None
# 2x2 grid 750x750 each tile 375? use 2x2 of 750
c=Image.new('RGB',(1500,1500),'white')
for i,t in enumerate(tiles): c.paste(t.resize((750,750)),((i%2)*750,(i//2)*750))
c.save(f'{out}/{site}_composite_2023-2025-maps.png'); print('composite')
