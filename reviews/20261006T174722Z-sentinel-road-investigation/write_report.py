from pathlib import Path
import json,html
from pyproj import Transformer
from PIL import Image
R=Path(__file__).parent
j=json.loads((R/'raster_audit.json').read_text())
# Coarse visually selected search rectangles, explicitly not road boundaries.
fwd=Transformer.from_crs(4326,3857,always_xy=True); inv=Transformer.from_crs(3857,4326,always_xy=True)
x0,y0=fwd.transform(24.4,58.2);x1,y1=fwd.transform(24.9,58.6)
boxes={'ROI-01':(.39,.12,.98,.47),'ROI-02':(.20,.02,.34,.30)}
features=[]
for name,(l,t,r,b) in boxes.items():
    xy=[(l,t),(r,t),(r,b),(l,b),(l,t)]
    coords=[inv.transform(x0+u*(x1-x0),y1-v*(y1-y0)) for u,v in xy]
    features.append({'type':'Feature','properties':{'id':name,'status':'candidate-search-region','uncertainty':'broad display-derived rectangle; not a surveyed road footprint','hypothesis':'diagonal linear corridor' if name=='ROI-01' else 'northwestern linear corridor'},'geometry':{'type':'Polygon','coordinates':[coords]}})
    for role in ('reference','target'):
        im=Image.open(R/f'{role}.png');w,h=im.size;im.crop((int(l*w),int(t*h),int(r*w),int(b*h))).save(R/f'{name}-{role}.png')
(R/'rois.geojson').write_text(json.dumps({'type':'FeatureCollection','features':features},indent=2))
blockers=['Actual portable-skill-bundle JSON and all four SKILL.md/reference files unavailable; prompt document and metric JSON cannot substitute for their bytes or hashes.','Supplied robust_threshold.py self-test, MAD/effect-size branch, and prespecified grid not executed: script and parameter contract unavailable.','ROI search rectangles are provisional; no exact road trace, width estimate, stable-control sample or registration residuals established.','Only one selected target optical acquisition is analyzed; persistence not executed. Additional target acquisition/cache availability not exhaustively evaluated.','No dated independent native-resolution before/after images downloaded or examined. Official orthophoto portal found, but per-ROI sheet dates, coverage and visibility not verified.','No construction/forestry/legal documents examined; no forest baseline supplied.','Browser rendering of interactive maps not available in the exposed tools; PNG figures inspected.']
claims={k:'unresolved' for k in ['linear_physical_change','road_identity','new_construction_vs_reopening_widening','appearance_interval','prior_forest','legal_attribution']}
findings={'status':'partial investigation; skill-dependent and corroboration work remains','claims':claims,'metrics':j,'blockers':blockers,'executed':['read-only graph validation','resolved outgoing semantic relationships with linked contextual corpus snapshot','tiled count and AND-mask reproduction','27-setting exploratory sigma/SAR count sensitivity','RGB and four-mask figure inspection','limited primary-source research','original run checksum preservation'],'unexecuted':blockers}
(R/'findings.json').write_text(json.dumps(findings,indent=2))
sources=[{'id':'ESA-radar','url':'https://www.esa.int/esapub/sp/sp1199/get21.htm','access':'full text read','claim':'Backscatter responds to roughness, humidity, polarization and incidence angle.','kg':['DS-0003','observation:sar-backscatter-state','method:s1-backscatter-confirmation']},{'id':'Oehmcke2019','url':'https://arxiv.org/abs/1912.05026','access':'full text read','claim':'Road visibility varies with width; supervised temporal models and fine labels address difficult roads. No validation of this NDVI/SAR rule.','kg':['DS-0002','observation:optical-vegetation-state'],'semantic_gap':'road identity and visibility-specific classifier'},{'id':'Congo-road-study','url':'https://www.sciencedirect.com/science/article/pii/S0034425724004061','access':'search abstract only; open failed','claim':'Multi-sensor road-development model reported in another geography; details and transferability unverified.'},{'id':'Estonian-orthophotos','url':'https://geoportaal.maaruum.ee/eng/spatial-data/orthophotos/download-orthophotos-p662.html','access':'official portal full text read; imagery not inspected','claim':'Official map-sheet download route exists; no site-specific dated corroboration obtained.'}]
(R/'literature_evidence.json').write_text(json.dumps(sources,indent=2))
(R/'literature_review.md').write_text('Partial primary-source review\n\nESA radar principles support several possible explanations for failure of a drop-only radar gate: roughness or wetness may maintain/increase backscatter. At a mixed 20 m analysis pixel a narrow corridor may occupy a small fraction. The latter is a mechanism hypothesis, not a measured result here. Single-June optical and summer-median radar also observe different temporal summaries. Oehmcke et al. demonstrate width-dependent visibility and use supervised models; their results do not validate this threshold rule. The Congo study is abstract-only evidence and cannot support detailed parameter choices. No source proves a road at these coordinates. Small reference samples and best-clear selection require context-specific validation; this limited review does not justify new calibrated thresholds. MAD remains an unexecuted proposal, and BFAST/CCDC were not attempted on the short series.\n\n'+ '\n'.join(f"- [{s['id']}]({s['url']}): {s['access']}. {s['claim']}" for s in sources))
ledger={'jurisdiction':'Estonia; AOI 24.4–24.9 E, 58.2–58.6 N','sources':[{'source':'Estonian-orthophotos','independence_group':'national-aerial-imagery','assessment':{k:'inconclusive' for k in claims},'imagery_access':'not yet acquired','dates':'not established'}],'first_appearance_interval':None}
(R/'independent_evidence_ledger.json').write_text(json.dumps(ledger,indent=2))
(R/'corroboration_report.md').write_text('Road and construction claims remain unresolved. The official Estonian orthophoto download portal was inspected, but no dated imagery was examined. The source therefore provides an access route, not corroboration. Per-ROI historical imagery with dates, adequate resolution and unobscured coverage is still required. Missing OSM features or editing dates cannot establish absence or construction timing. Prior forest and legal attribution require separate evidence.\n')
(R/'candidates').mkdir(exist_ok=True)
proposal={'status':'candidate','human_review_required':True,'title':'Preserve optical/SAR disagreement when investigating linear infrastructure','sources':['raster_audit.json','literature_evidence.json','semantic_trace.json'],'existing_concepts':['method:s1-backscatter-confirmation','method:ndvi-anomaly','claim:monthly-non-truth'],'proposed_context':'A failed AND gate does not refute physical road existence; evaluate dated independent imagery and separate construction, widening/reopening, forest and legality claims.','contradictions':'No site-specific labels or independent dated evidence; thresholds remain heuristic.','promotion':'Not submitted to canonical corpus or generated graph.'}
(R/'candidates/index.json').write_text(json.dumps([proposal],indent=2))
rows='\n'.join(f"| {k} | {v['anomaly_pixels']:,} | {v['anomaly_ha']:,.2f} | {v['valid_pixels']:,} |" for k,v in j['counts'].items())
md=f'''# Sentinel linear-feature review — partial evidence report

The available analysis does not establish a newly constructed road. All six site-specific claims remain unresolved. The reduction in red area is explained by the configured AND rule, not demonstrated improvement in accuracy.

| Variant | Candidate pixels | Candidate ha | Valid pixels |
|---|---:|---:|---:|
{rows}

Fixed NDVI retains 9,469 of 91,291 candidates after SAR (10.37%); sigma retains 12,875 of 121,242 (10.62%). Fixed comparison: 81,822 optical-only, 110,124 radar-only, 3,053,891 neither on 3,255,306 jointly valid pixels. Sigma: 108,367 optical-only, 106,719 radar-only, 3,027,390 neither on 3,255,351 jointly valid pixels. Optical-valid/radar-unavailable is zero for both. Grid-exterior/nodata counts are recorded separately in raster_audit.json.

The strict gate requires ΔVV < −1.5 dB AND ΔVH < −1 dB alongside optical detection. Rejected optical candidates fail at least one radar condition. Radar-only is a screening classification, not road evidence. Raw RGB comparisons show multiple candidate corridors; rois.geojson contains two broad search regions, not certified road traces. Images use identical footprint and stretch; visual alignment is not a quantified registration test. Apparent width has not been measured.

Optical target: 20 June 2026. Sigma optical reference: eight selected 2025 summer dates. Display reference: 15 June 2025, a single scene, distinct from the sigma mean. Radar: twelve selected dates per summer, ascending relative orbit 160, median in dB. This temporal mismatch may suppress transient/local changes; it does not establish a construction date. Cloud-edge mixing, phenology, agriculture, moisture and mixed pixels remain alternatives. No forest mask was applied.

Executed exploratory sensitivity uses k={{1,2,3}}, VV={{−1,−1.5,−2}} dB, VH={{−0.5,−1,−1.5}} dB, all 27 combinations saved in sigma_sar_sensitivity.json. This is an independently declared count experiment, not the missing skill's prespecified experiment, a probability or accuracy validation. No experimental robust masks/maps were produced.

KG check passed without writing, revision ef90b703ae150c09cc7cac6fd324d7b5ecd8305a5a0d5130ec0deb61ed291e49. Commit, worktree state, traversed nodes/edges and context hashes are pinned in semantic_trace.json. Linked corpus and contract records are copied under semantic_context/. Candidate edges remain candidates; contract-transcription validation is not empirical validation. The local candidate package is candidates/index.json; no canonical knowledge was changed.

Original run and source-run files were hashed before and after audit: original_integrity.json reports unchanged. Reproduce with `.venv/bin/python reviews/{R.name}/audit.py`; reports are generated by write_report.py. Inputs, copies and all results stay under this REVIEW. No Earth Engine dependency was used.

Remaining work and blockers:

'''+ '\n'.join('- '+b for b in blockers)+'\n\nSee literature_review.md and independent_evidence_ledger.json for source access limits.\n'
(R/'report.md').write_text(md)
links=['maps/comparison.html','raster_audit.json','sigma_sar_sensitivity.json','semantic_trace.json','findings.json','rois.geojson','literature_review.md','independent_evidence_ledger.json','candidates/index.json']
body='<html><meta charset="utf-8"><title>Sentinel review</title><style>body{max-width:1100px;margin:30px auto;font:16px sans-serif}img{max-width:100%}pre{white-space:pre-wrap} .pair{display:flex}.pair img{width:49%}</style><body><pre>'+html.escape(md)+'</pre><img src="four_map_contact_sheet.jpg"><h2>Matched RGB search-region crops, overlays off</h2>'
for name in boxes:body+=f'<p>{name}: reference left, target right. Display-derived search extent; no measured road boundary.</p><div class="pair"><img src="{name}-reference.png"><img src="{name}-target.png"></div>'
body+='<ul>'+''.join(f'<li><a href="{p}">{p}</a></li>' for p in links)+'</ul></body></html>'
(R/'report.html').write_text(body)
for p in links:assert (R/p).exists(),p
print('Report links verified; staged partial report and candidate package.')
