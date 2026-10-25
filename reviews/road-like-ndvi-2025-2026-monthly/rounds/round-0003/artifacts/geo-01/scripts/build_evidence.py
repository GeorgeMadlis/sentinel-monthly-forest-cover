"""Build geo_primary_evidence.json: hashes of all source/derived artifacts with dates, licence and lineage."""
import json,hashlib,pathlib,sys,datetime
A=pathlib.Path(sys.argv[1])
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
fetch={pathlib.Path(r['file']).name:r for r in map(json.loads,open(A/'raw/fetch_log.jsonl'))}
acq={'of2023mets':'2023-06-09','of2024asulad':'2024-05-03 (ROI-01 SW sheets 476534/478535)','of2025aero':'2025-04-03','EESTIFOTO':'2025-04-03 (current = of2025aero here)'}
lin={'of2023mets':'LG-MARU-ORTHO-2023','of2024asulad':'LG-MARU-ORTHO-2024','of2025aero':'LG-MARU-ORTHO-2025','EESTIFOTO':'LG-MARU-ORTHO-2025','pk_vr2024':'LG-MARU-ETAK','pk_vr2026':'LG-MARU-ETAK'}
items=[]
for p in sorted(A.rglob('*')):
    if p.is_dir() or p.name in ('geo_primary_evidence.json','execution.json') or '__pycache__' in p.parts: continue
    rel=str(p.relative_to(A)); kind=rel.split('/')[0]
    e={'path':rel,'sha256':h(p),'bytes':p.stat().st_size,'kind':{'raw':'source_download','images':'derived_image','scripts':'helper_script'}.get(kind,'output_table_or_doc')}
    layer=next((k for k in acq if k in p.name),None) or next((k for k in lin if k in p.name),None)
    if p.name in fetch:
        r=fetch[p.name]; e.update(url=r['url'],retrieved_utc=r['retrieved_utc'],bbox_epsg3301=r['bbox_epsg3301_xmin_ymin_xmax_ymax'],display_pixel_m=r['pixel_m'])
    if layer:
        e['layer']=layer; e['acquisition_date']=acq.get(layer,'n/a (map edition '+layer[-4:]+')'); e['source_lineage']=lin.get(layer)
    if kind in ('raw','images'): e['license']='Maa- ja Ruumiamet open data licence (https://geoportaal.maaruum.ee/avaandmete-litsents); attribution: Maa- ja Ruumiamet, retrieved 2026-10-24'
    if kind=='images': e['derived_from']='raw/wms/'+p.name.split('_flight')[0].split('_map-edition')[0].replace('_composite','')+'.*' ; e['processing']='ROI outline (inputs/prior_rois.geojson reprojected to EPSG:3301), caption, 100 m scale bar; composites resized'
    items.append(e)
out={'schema':'geo-01 primary evidence v1','generated_utc':datetime.datetime.now(datetime.timezone.utc).strftime('%FT%TZ'),
 'roi_input':{'path':'inputs/prior_rois.geojson','sha256':'b079d3dbff8a473daf6e3d33cdfdaedffc29de470425b8fe9a212f796a862125'},
 'crs':'EPSG:3301 for all WMS/WFS requests (WMS 1.3.0 BBOX axis order northing,easting)',
 'resolved_flight_dates':json.load(open(A/'raw/sheets/sheet_dates_summary.json')),
 'missing_inputs':[
  {'item':'orthophoto acquired after 2025-04-03 (post-July-2025) for ROI sheets','status':'unavailable','checked':'per-sheet listings GS-05/GS-06, WMS capabilities (no of2026*), EESTIFOTO equality check'},
  {'item':'2024 orthophoto for ROI-01 (except SW end) and ROI-02','status':'unavailable','checked':'GS-05/GS-06'},
  {'item':'historical ETAK vector editions (dated snapshots)','status':'not_retrieved','note':'pk_vr2024/pk_vr2026 raster editions used instead'},
  {'item':'orthophoto positional-accuracy statement per flight','status':'not_retrieved'},
  {'item':'orthophoto windows for CONTROL-01/02','status':'not_requested (image budget)'}],
 'lineage_note':'All sources are Maa- ja Ruumiamet products. Orthophoto flights of different dates are separate acquisitions but share producer and processing chain; ETAK/basic maps are partly derived from these orthophotos, so map and image evidence are not independent lineages.',
 'artifacts':items}
json.dump(out,open(A/'geo_primary_evidence.json','w'),indent=1,ensure_ascii=False); print(len(items),'artifacts')
