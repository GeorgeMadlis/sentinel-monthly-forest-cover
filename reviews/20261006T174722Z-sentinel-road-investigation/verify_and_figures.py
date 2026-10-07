from pathlib import Path
import sys,json,importlib.util
import numpy as np,rasterio
from PIL import Image,ImageDraw
from contextlib import ExitStack
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from forest_change.evidence import checksum,write_json
from forest_change.leaflet import visual_grid,anomaly_rgba
from forest_change.raster import read_asset
from forest_change.providers import LocalRasterProvider
from rasterio.windows import Window
from rasterio.features import geometry_mask
from rasterio.warp import transform_geom
R=Path(__file__).resolve().parent;RUN=R.parents[1]/'runs/aoi-s2-s1-jja-2025-2026-sigma';base=Path(json.loads((RUN/'maps/map_metadata.json').read_text())['source_run'])
manifest=json.loads((RUN/'run_manifest.json').read_text());outputs=[]
for o in manifest['outputs']:
 p=RUN/o['path'];actual=checksum(p) if p.exists() else None;outputs.append({'path':o['path'],'expected':o.get('sha256'),'actual':actual,'matches':actual==o.get('sha256')})
write_json(R/'manifest_verification.json',{'outputs':outputs,'all_match':all(x['matches'] for x in outputs)})
spec=importlib.util.spec_from_file_location('build',Path('/Users/server/projects/forest-cover-lab/graph/build.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
g=json.loads(Path('/Users/server/projects/forest-cover-lab/graph/generated/knowledge.json').read_text())
try:m.validate_provenance(manifest,g);provenance={'status':'passed','comparison':'current pinned graph'}
except Exception as ex:provenance={'status':'failed','error':str(ex),'note':'Run was not edited; pinned historical context may differ.'}
write_json(R/'provenance_validation.json',provenance)
records=json.loads((R/'threshold_experiments.json').read_text())['settings']
sheet=Image.new('RGB',(6*210,3*390),'white');d=ImageDraw.Draw(sheet)
for i,record in enumerate(records):
 x=(i%6)*210;y=(i//6)*390;d.text((x+3,y+3),f"k={record['k']} drop={record['delta_min']} floor={record['epsilon']}",fill='black')
 for j,mode in enumerate(('optical','and','or')):
  folder=(R/record['artifacts']['optical.tif']['path']).parent/f'maps_{mode}'
  bg=Image.open(folder/'target.png').convert('RGBA');ov=Image.open(folder/'anomalies.png').convert('RGBA');img=Image.alpha_composite(bg,ov);img.thumbnail((65,340));sheet.paste(img.convert('RGB'),(x+j*69,y+32));d.text((x+j*69,y+17),mode,fill='black')
sheet.save(R/'robust_contact_sheet.png');Image.open(R/'four_map_contact_sheet.jpg').save(R/'contact_sheet.png')
# Individual georeferenced sampling figures on original 20 m grid.
rois=json.loads((R/'rois.geojson').read_text())['features']
provider=LocalRasterProvider({'inventory':str(RUN/'optical_inventory.json'),'collection':'archived-calibrated'})
with rasterio.open(RUN/'w0000/NDVI_current.tif') as s:
 for roi in rois[:2]:
  geom=transform_geom('EPSG:4326',s.crs,roi['geometry']);from rasterio.features import geometry_window
  w=geometry_window(s,[geom],pad_x=5,pad_y=5);w=w.round_offsets().round_lengths()
  # Persist multi-band RGB georeferenced crops, analytical resolution only.
  for role in ('reference','target'):
   assets=base/'source_windows'/role
   bands=[]
   for band in ('red','green','blue'):
    with rasterio.open(assets/(band+'.tif')) as source:bands.append(source.read(1,window=w,masked=True).filled(np.nan))
   values=np.stack(bands);prof=s.profile.copy();prof.update(count=3,width=int(w.width),height=int(w.height),transform=rasterio.windows.transform(w,s.transform))
   p=R/f"{roi['properties']['id']}-{role}-georef.tif"
   with rasterio.open(p,'w',**prof) as dst:dst.write(np.where(np.isfinite(values),values,-9999))
# Approximate local registration using unchanged-looking landmark patches; integer shifts, no correction.
from forest_change.raster import Grid
with rasterio.open(RUN/'w0000/NDVI_current.tif') as s:grid=Grid(str(s.crs),s.transform,s.width,s.height)
landmarks=[('Pärnu urban crossing',300,610),('existing road junction',1830,420)]
reg=[]
for name,col,row in landmarks:
 w=Window(col,row,40,40);images=[]
 for role in ('reference','target'):
  arr=[]
  for band in ('red','green','blue'):
   with rasterio.open(base/'source_windows'/role/(band+'.tif')) as src:arr.append(src.read(1,window=w,masked=True).filled(np.nan))
  images.append(np.nanmean(arr,axis=0))
 a,b=images;sc=[]
 for dy in range(-2,3):
  for dx in range(-2,3):
   core=a[3:-3,3:-3];other=b[3+dy:37+dy,3+dx:37+dx];v=np.isfinite(core)&np.isfinite(other)
   if v.sum()>30:sc.append((float(np.corrcoef(core[v],other[v])[0,1]),dx,dy))
 best=max(sc);zero=next(q[0] for q in sc if q[1:]==(0,0));reg.append({'landmark':name,'window':[col,row,40,40],'best_integer_shift_pixels':[best[1],best[2]],'correlation':best[0],'zero_shift_correlation':zero,'resolution_m':20,'uncertainty':'local radiometric/seasonal correlation only, not surveyed subpixel geolocation accuracy','action':'no shift applied'})
write_json(R/'registration_check.json',reg)
# Preserve original hashes from first stage, check after all work.
before=json.loads((R/'original_hashes_before.json').read_text());changed=[p for p,h in before.items() if checksum(p)!=h]
write_json(R/'original_integrity.json',{'files_checked':len(before),'unchanged':not changed,'changed':changed})
print(json.dumps({'manifest_mismatches':[x['path'] for x in outputs if not x['matches']],'provenance':provenance,'registration':reg,'originals_unchanged':not changed},indent=2))
