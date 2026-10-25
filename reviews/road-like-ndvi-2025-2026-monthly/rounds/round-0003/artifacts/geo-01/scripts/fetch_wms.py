"""Fetch a small WMS GetMap window (EPSG:3301, WMS 1.3.0 axis order N,E) and log provenance.
usage: fetch_wms.py SERVICE LAYERS CX CY HALF_M PX OUTFILE [FORMAT] [TRANSPARENT]"""
import sys, hashlib, json, datetime, urllib.request, urllib.parse, pathlib
svc,layers,cx,cy,half,px,out=sys.argv[1:8]
fmt=sys.argv[8] if len(sys.argv)>8 else 'image/png'
transp=sys.argv[9] if len(sys.argv)>9 else 'FALSE'
cx,cy,half,px=float(cx),float(cy),float(half),int(px)
p={'SERVICE':'WMS','VERSION':'1.3.0','REQUEST':'GetMap','LAYERS':layers,'STYLES':'','CRS':'EPSG:3301',
   'BBOX':f'{cy-half:.0f},{cx-half:.0f},{cy+half:.0f},{cx+half:.0f}','WIDTH':px,'HEIGHT':px,'FORMAT':fmt,'TRANSPARENT':transp}
url=f'https://kaart.maaamet.ee/wms/{svc}?'+urllib.parse.urlencode(p)
t=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
req=urllib.request.Request(url,headers={'User-Agent':'geo-01-research/1.0'})
data=urllib.request.urlopen(req,timeout=120).read()
pathlib.Path(out).write_bytes(data)
rec={'file':out,'url':url,'retrieved_utc':t,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),
     'bbox_epsg3301_xmin_ymin_xmax_ymax':[cx-half,cy-half,cx+half,cy+half],'pixel_m':2*half/px,'service':svc,'layers':layers}
log=pathlib.Path(out).parent.parent/'fetch_log.jsonl'
with open(log,'a') as f: f.write(json.dumps(rec)+'\n')
print(json.dumps(rec))
