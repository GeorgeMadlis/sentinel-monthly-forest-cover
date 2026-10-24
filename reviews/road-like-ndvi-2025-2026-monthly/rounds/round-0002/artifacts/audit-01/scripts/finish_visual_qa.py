"""Render already-reproduced cached decisions on exact prior sampling windows."""
from pathlib import Path
import hashlib
import html
import json
import shutil
import sys
import numpy as np
import rasterio
from rasterio.windows import Window
from PIL import Image, ImageDraw

OUT=Path(__file__).resolve().parents[1]
ROOT=OUT.parents[5]
sys.path.insert(0,str(ROOT))
from forest_change.bundle import page

qa=json.loads((OUT/'geometry_qa.json').read_text())
payload={}
for f in qa['features']:
    rid=f['roi_id'];folder=OUT/'inspect/crops';images=[]
    for role in ['reference','target']:
        for variant in ['raw','outline']:
            images.append(Image.open(folder/f'{rid}-{role}-{variant}.png').convert('RGB'))
    cw=max(i.width for i in images)+20;ch=max(i.height for i in images)+35
    sheet=Image.new('RGB',(2*cw,2*ch),'white');draw=ImageDraw.Draw(sheet)
    for j,img in enumerate(images):
        x=j%2*cw;y=j//2*ch;sheet.paste(img,(x+8,y+28))
        draw.text((x+8,y+8),rid+' '+['2025 raw','2025 outline','2026 raw','2026 outline'][j],fill='black')
    sheet.save(OUT/'inspect'/f'{rid}-compact.png')
    window=Window(*f['sampling_window_pixels'])
    raw=Image.open(folder/f'{rid}-target-raw.png').convert('RGBA')
    layers={name:'crops/'+rid+'-target-'+name+'.png' for name in ['raw','outline']}
    for n in ['fixed','fixed_and_radar','sigma','sigma_and_radar']:
        with rasterio.open(OUT/'recomputed'/f'{n}.tif') as src:
            a=src.read(1,window=window,masked=True).filled(np.nan)
        rgba=np.zeros((*a.shape,4),dtype='uint8');rgba[a==1]=[255,0,0,210];rgba[~np.isfinite(a)]=[90,90,90,190]
        mask=Image.fromarray(rgba).resize(raw.size,Image.Resampling.NEAREST)
        dest=folder/f'{rid}-{n}.png';Image.alpha_composite(raw,mask).save(dest)
        layers[n]='crops/'+dest.name
    payload[rid]=layers
data=json.dumps(payload).replace('<','\\u003c')
body='''<h1>Audit of archived signal and sampling polygons</h1>
<p>Only cached observations: 15 June 2025 and 20 June 2026 RGB. No monthly mean or forest baseline.
Yellow/blue outlines are archived sampling polygons, not measured road edges. Red denotes a reproduced candidate;
gray indicates unavailable decision evidence. These are the original rules, not new thresholds.</p>
<label>ROI <select id="roi">'''+''.join('<option>'+rid+'</option>' for rid in payload)+'''</select></label>
<label>View <select id="layer"><option value="raw">2026 raw RGB</option><option value="outline">2026 sampling outline</option>
<option value="fixed">Fixed optical</option><option value="fixed_and_radar">Fixed optical AND radar</option>
<option value="sigma">Sigma optical</option><option value="sigma_and_radar">Sigma optical AND radar</option></select></label>
<p><img id="evidence" alt="Selected cached audit view"></p>
<p>Compare fixed vs fixed AND radar, and sigma vs sigma AND radar. Sigma uses eight summer 2025 dates,
not the single RGB reference date. Radar uses summer medians on ascending relative orbit 160.</p>
<script>const data='''+data+''';const roi=document.getElementById('roi'),layer=document.getElementById('layer');
function show(){document.getElementById('evidence').src=data[roi.value][layer.value];}
roi.onchange=show;layer.onchange=show;show();</script>'''
(OUT/'inspect/comparison.html').write_text(page('Local-only audit comparison',body))
# Source/retrieval dates and actual URLs are read from archived local records only.
assets=json.loads((OUT/'authenticated_inputs.json').read_text())['assets'];dates=[]
for a in assets:
    p=ROOT/a['source'].removeprefix('sentinel-local:');sidecar=p.with_suffix('.json')
    m=json.loads(sidecar.read_text()) if sidecar.exists() else {}
    dates.append({'item_id':a['item_id'],'band':a['band'],'acquisition_utc':a['acquisition_utc'],
        'historical_retrieval_utc':m.get('acquired_at','not_exposed_in_this_sidecar'),
        'source_url':a['source_url'],'source_sha256':a['sha256'],'lineage':a['lineage']})
(OUT/'source_dates.json').write_text(json.dumps(dates,indent=2)+'\n')
print('Rendered compact figures, per-ROI reproduced overlays and offline comparison; no source imagery fetched')
