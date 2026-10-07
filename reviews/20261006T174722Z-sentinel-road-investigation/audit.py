from pathlib import Path
import sys,json,subprocess,shutil
from contextlib import ExitStack
import numpy as np
import rasterio
from PIL import Image,ImageDraw
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from forest_change.evidence import checksum,write_json
R=Path(__file__).resolve().parent
RUN=R.parents[1]/'runs/aoi-s2-s1-jja-2025-2026-sigma'
LAB=Path('/Users/server/projects/forest-cover-lab')
base=Path(json.loads((RUN/'maps/map_metadata.json').read_text())['source_run'])
files={'sigma':RUN/'maps_ndvi_sigma_mask.tif','sigma_sar':RUN/'maps_mask.tif','fixed_sar':RUN/'maps_fixed_sar_mask.tif','fixed':base/'w0000/disturbance.tif','sar':RUN/'w0000/sar_candidate.tif','vv':RUN/'w0000/VV_change.tif','vh':RUN/'w0000/VH_change.tif','change':RUN/'w0000/NDVI_change.tif','std':RUN/'w0000/NDVI_reference_std.tif','count':RUN/'w0000/NDVI_reference_count.tif'}
original={str(p):checksum(p) for root in (RUN,base) for p in root.rglob('*') if p.is_file()}
write_json(R/'original_hashes_before.json',original)
counts={k:{'anomaly_pixels':0,'valid_pixels':0} for k in ('fixed','fixed_sar','sigma','sigma_sar')}
comparison={k:dict.fromkeys(('joint_valid','agreement','optical_only','radar_only','neither','unavailable','optical_valid_radar_unavailable'),0) for k in ('fixed','sigma')}
sensitivity=[]
settings=[(k,v,h) for k in (1,2,3) for v in (-1.,-1.5,-2.) for h in (-.5,-1.,-1.5)]
totals={x:[0,0,0] for x in settings}
with ExitStack() as stack:
    src={k:stack.enter_context(rasterio.open(p)) for k,p in files.items()}
    first=src['sigma']
    for s in src.values():
        assert (s.crs,s.transform,s.width,s.height)==(first.crs,first.transform,first.width,first.height)
    pixel_ha=abs(first.transform.a*first.transform.e)/10000
    grid={'crs':str(first.crs),'transform':list(first.transform),'width':first.width,'height':first.height,'pixel_ha':pixel_ha}
    for _,w in first.block_windows(1):
        a={k:s.read(1,window=w,masked=True).filled(np.nan) for k,s in src.items()}
        for k in counts:
            counts[k]['valid_pixels']+=int(np.isfinite(a[k]).sum()); counts[k]['anomaly_pixels']+=int((a[k]==1).sum())
        for k in comparison:
            o=a[k]; s=a['sar']; valid=np.isfinite(o)&np.isfinite(s); c=comparison[k]
            for label,m in {'joint_valid':valid,'agreement':valid&(o==1)&(s==1),'optical_only':valid&(o==1)&(s==0),'radar_only':valid&(o==0)&(s==1),'neither':valid&(o==0)&(s==0),'unavailable':~valid,'optical_valid_radar_unavailable':np.isfinite(o)&~np.isfinite(s)}.items():c[label]+=int(m.sum())
            assert np.all(a[k+'_sar'][valid]==((o[valid]==1)&(s[valid]==1)))
        valid=np.isfinite(a['change'])&np.isfinite(a['std'])&(a['std']>0)&(a['count']>=2)
        rv=np.isfinite(a['vv'])&np.isfinite(a['vh']); support=valid&rv
        for setting,t in totals.items():
            k,v,h=setting; o=valid&(a['change'] < -k*a['std']); sar=rv&(a['vv']<v)&(a['vh']<h)
            t[0]+=int(valid.sum());t[1]+=int(o.sum());t[2]+=int((o&sar).sum())
    for c in counts.values():c['anomaly_ha']=round(c['anomaly_pixels']*pixel_ha,2)
    for setting,t in totals.items():sensitivity.append(dict(zip(('k','vv_drop_db','vh_drop_db'),setting))|{'optical_valid_pixels':t[0],'optical_candidate_pixels':t[1],'combined_candidate_pixels':t[2]})
write_json(R/'raster_audit.json',{'grid':grid,'counts':counts,'comparison':comparison,'support_note':'Unavailable counts include grid exterior; joint-valid denominators exclude nodata. Radar-only means threshold-positive optical-negative, not a road label.'})
write_json(R/'sigma_sar_sensitivity.json',{'status':'executed independently of unavailable bundled helper','settings':sensitivity,'heuristic':True,'not_accuracy_validation':True})
# Follow resolved outgoing KG relations and preserve full contextual corpus plus sources.
g=json.loads((LAB/'graph/generated/knowledge.json').read_text()); nodes={n['id']:n for n in g['nodes']}; edges=g['relationships']+g['candidate_relationships']
seen=set(); todo=['workflow:sentinel-monthly-forest-cover','application:seasonal-forest-change-monitoring']
while todo:
    x=todo.pop()
    if x in seen:continue
    assert x in nodes;seen.add(x)
    todo += [e['target'] for e in edges if e['source']==x and e['target'] not in seen]
selected=[e for e in edges if e['source'] in seen]
paths={n['path'] for n in nodes.values() if n['id'] in seen}
for n in nodes.values():
    if n['id'] in seen:paths.update(n.get('sources',[]))
for e in selected:paths.update(e.get('sources',[]))
for p in sorted(paths):
    source=LAB/p
    if source.is_file():
        dst=R/'semantic_context'/p;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dst)
write_json(R/'semantic_trace.json',{'graph_revision':g['revision'],'graph_check':'68 concepts; 72 validated and 67 candidate relationships; check passed without writing','lab_commit':subprocess.check_output(['git','-C',str(LAB),'rev-parse','HEAD'],text=True).strip(),'repo_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'lab_worktree':subprocess.check_output(['git','-C',str(LAB),'status','--porcelain'],text=True),'repo_worktree':subprocess.check_output(['git','status','--porcelain'],text=True),'nodes':[nodes[x] for x in sorted(seen)],'relationships':selected,'context_hashes':{p:checksum(LAB/p) for p in sorted(paths) if (LAB/p).is_file()},'authority_note':'Validated contract-transcription edges are not empirical accuracy or road validation. Candidate edges remain candidates.'})
# Portable original comparison, identical backgrounds, downsampled static contact sheet.
for folder in ('maps_original','maps_fixed_sar','maps_ndvi_sigma','maps'):shutil.copytree(RUN/folder,R/'maps'/folder,dirs_exist_ok=True)
shutil.copyfile(RUN/'comparison.html',R/'maps/comparison.html')
sheet=Image.new('RGB',(1200,1050),'white'); d=ImageDraw.Draw(sheet)
for i,folder in enumerate(('maps_original','maps_fixed_sar','maps_ndvi_sigma','maps')):
    bg=Image.open(RUN/folder/'target.png').convert('RGBA');mask=Image.open(RUN/folder/'anomalies.png').convert('RGBA')
    assert bg.size==mask.size
    bg=Image.alpha_composite(bg,mask);bg.thumbnail((280,920));sheet.paste(bg.convert('RGB'),(i*300,60));d.text((i*300+5,15),folder,fill='black')
sheet.save(R/'four_map_contact_sheet.jpg',quality=92)
for role in ('reference','target'):shutil.copyfile(RUN/'maps'/f'{role}.png',R/f'{role}.png')
after={p:checksum(p) for p in original};write_json(R/'original_integrity.json',{'files_checked':len(original),'unchanged':after==original})
print(json.dumps({'counts':counts,'comparison':comparison,'context_records':len(paths),'original_files_unchanged':after==original},indent=2))
