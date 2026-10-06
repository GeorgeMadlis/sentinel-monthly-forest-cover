"""Portable RGB/anomaly overlays on a common Web Mercator visualization grid."""
import base64
import html
import json
from pathlib import Path
import numpy as np
import rasterio
from affine import Affine
from PIL import Image
from rasterio.enums import Resampling
from rasterio.warp import transform_bounds, transform_geom
from rasterio.windows import Window
from shapely.geometry import shape
from .raster import Grid, read_asset, inside
from .asset_access import download


def anomaly_rgba(values):
    rgba = np.zeros((*values.shape,4), dtype='uint8')
    rgba[values == 1] = [255,0,0,210]
    return rgba


def visual_grid(geometry, width=1400):
    left,bottom,right,top = transform_bounds('EPSG:4326','EPSG:3857',*shape(geometry).bounds)
    height = round(width*(top-bottom)/(right-left))
    return Grid('EPSG:3857', Affine((right-left)/width,0,left,0,-(top-bottom)/height,top),width,height)


def prepare_overlays(out, geometry, selected, provider, anomaly_path):
    out=Path(out); out.mkdir(parents=True,exist_ok=True)
    grid=visual_grid(geometry)
    win=Window(0,0,grid.width,grid.height)
    gate=inside(transform_geom('EPSG:4326',grid.crs,geometry),grid,win)
    for role, record in selected.items():
        item=record['item']
        bands=[read_asset(provider,item['assets'][key],grid,win) for key in ('red','green','blue')]
        scl=read_asset(provider,item['assets']['scl'],grid,win,categorical=True)
        valid=gate & np.isin(scl,[4,5,6,7]) & np.logical_and.reduce([np.isfinite(b) for b in bands])
        rgb=np.stack(bands,axis=-1)
        # Fixed reflectance range and gamma, identical on both dates.
        rgba=np.zeros((grid.height,grid.width,4),dtype='uint8')
        rgba[:,:,:3]=(255*np.power(np.clip(np.nan_to_num(rgb)/.3,0,1),1/2.2)).astype('uint8')
        rgba[:,:,3]=valid.astype('uint8')*255
        Image.fromarray(rgba).save(out/(role+'.png'))
    values=read_asset(provider,{'href':str(anomaly_path)},grid,win,categorical=True)
    Image.fromarray(anomaly_rgba(np.where(gate,values,np.nan))).save(out/'anomalies.png')
    left,bottom,right,top=transform_bounds(grid.crs,'EPSG:4326',*rasterio.transform.array_bounds(grid.height,grid.width,grid.transform))
    return [[bottom,left],[top,right]]


def generate_map(path, geometry, bounds, selected, metadata):
    path=Path(path)
    def data(name):
        return 'data:image/png;base64,'+base64.b64encode((path.parent/name).read_bytes()).decode()
    labels={role:f'{role.title()} Sentinel-2 — {r["item"]["datetime"][:10]}' for role,r in selected.items()}
    payload={'aoi':geometry,'bounds':bounds,'labels':labels,'images':{n:data(n+'.png') for n in ('reference','target','anomalies')}}
    panel=html.escape(json.dumps(metadata,indent=2))
    compact='<p><b>Run:</b> '+html.escape(str(metadata.get('run_id','')))+'</p>'
    for role,record in selected.items():
        period=record.get('period',{})
        period_text=period.get('start','')+' — '+period.get('end','')
        compact+='<p><b>'+role.title()+':</b> '+html.escape(period_text) + '<br>'+html.escape(record['item']['id'])+'<br>'+html.escape(record['item']['datetime'])+'</p>'
    threshold=metadata.get('threshold','')
    threshold_text=('target − reference < '+str(threshold.get('value'))) if isinstance(threshold,dict) and threshold.get('mode')=='fixed' else str(threshold)
    compact+='<p><b>Method:</b> '+html.escape(str(metadata.get('method','NDVI target minus reference'))) + '<br><b>Threshold:</b> '+html.escape(threshold_text)+'</p>'
    script='''const d=PAYLOAD;const map=L.map('map',{zoomSnap:0.1});
map.createPane('anomalies');map.getPane('anomalies').style.zIndex=450;
const reference=L.imageOverlay(d.images.reference,d.bounds,{attribution:'Sentinel-2 / Copernicus; Earth Search / Element 84'}),target=L.imageOverlay(d.images.target,d.bounds,{attribution:'Sentinel-2 / Copernicus; Earth Search / Element 84'}).addTo(map);
const anomalies=L.imageOverlay(d.images.anomalies,d.bounds,{pane:'anomalies'}).addTo(map);
const aoi=L.geoJSON(d.aoi,{style:{color:'#ffff00',weight:2,fill:false}}).addTo(map);
L.control.layers({}, {[d.labels.reference]:reference,[d.labels.target]:target,'Detected anomalies':anomalies},{collapsed:false}).addTo(map);
L.control.scale().addTo(map);map.fitBounds(aoi.getBounds());'''.replace('PAYLOAD',json.dumps(payload).replace('<','\\u003c'))
    path.write_text('''<!doctype html><html><head><meta charset="utf-8"><title>Sentinel-2 anomaly evidence</title>
<link rel="stylesheet" href="leaflet.css"><script src="leaflet.js"></script>
<style>body{margin:0;font:14px sans-serif}#map{height:100vh}.info{position:absolute;bottom:30px;left:12px;z-index:1000;background:white;padding:12px;max-width:420px;max-height:40vh;overflow:auto}pre{white-space:pre-wrap;font-size:11px}</style></head><body>
<div id="map"></div><div class="info"><b>Detected anomalies</b><p><span style="color:red">■</span> Red: NDVI decline exceeding threshold; transparent: absence or unavailable data.</p><p>Candidate change, not confirmed deforestation. Yellow: AOI.</p>'''+compact+'<details><summary>Full provenance</summary><pre>'+panel+'</pre></details></div><script>'+script+'</script></body></html>')
    return path


def vendor_leaflet(directory):
    directory=Path(directory)
    (directory/'images').mkdir(parents=True,exist_ok=True)
    files=['leaflet.js','leaflet.css'] + ['images/'+n for n in
        ('layers.png','layers-2x.png','marker-icon.png','marker-icon-2x.png','marker-shadow.png')]
    for filename in files:
        destination=directory/filename
        if not destination.exists():
            download('https://unpkg.com/leaflet@1.9.4/dist/'+filename,destination)
