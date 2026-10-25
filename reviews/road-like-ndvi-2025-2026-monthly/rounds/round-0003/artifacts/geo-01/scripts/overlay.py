"""Draw ROI polygon outlines (inputs/prior_rois.geojson, reprojected to EPSG:3301) and a caption onto a WMS image.
usage: overlay.py ROIS_GEOJSON IN_IMG XMIN YMIN XMAX YMAX OUT_PNG CAPTION [MAXPX]"""
import sys,json
from PIL import Image,ImageDraw
from pyproj import Transformer
from shapely.geometry import shape
from shapely.ops import transform
g=json.load(open(sys.argv[1])); src=sys.argv[2]; x0,y0,x1,y1=map(float,sys.argv[3:7]); out=sys.argv[7]; cap=sys.argv[8]
maxpx=int(sys.argv[9]) if len(sys.argv)>9 else 1500
tr=Transformer.from_crs(4326,3301,always_xy=True).transform
im=Image.open(src).convert('RGB'); W,H=im.size; d=ImageDraw.Draw(im)
def px(x,y): return ((x-x0)/(x1-x0)*W,(y1-y)/(y1-y0)*H)
for f in g['features']:
    geom=transform(tr,shape(f['geometry']))
    polys=[geom] if geom.geom_type=='Polygon' else list(geom.geoms)
    for p in polys:
        d.line([px(*c) for c in p.exterior.coords],fill=(255,0,255),width=max(1,W//500))
    lab=f['properties'].get('roi_id') or f['properties'].get('id') or ''
    c=geom.representative_point()
d.rectangle([0,0,W,16],fill=(0,0,0)); d.text((3,2),cap,fill=(255,255,0))
if max(W,H)>maxpx: im.thumbnail((maxpx,maxpx))
im.save(out); print(out,im.size)
