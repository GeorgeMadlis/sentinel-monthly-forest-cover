"""Write the audit ledgers/report and a separately pinned derived-run manifest."""
from copy import deepcopy
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import jsonschema
import numpy as np
import rasterio
import pyproj
import shapely
import yaml

OUT=Path(__file__).resolve().parents[1];ROOT=OUT.parents[5];LAB=ROOT.parent/'forest-cover-lab';RD=OUT.parents[1]
sys.path.insert(0,str(ROOT))
from forest_change.bundle import page


def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(name,d): (OUT/name).write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')


authentication=load(OUT/'cache_authentication.json');reproduction=load(OUT/'reproduction.json')
assert reproduction['continuous_reproduction_pass'] and reproduction['production_mask_reproduction_pass']
assert load(OUT/'original_integrity.json')['unchanged']
spec=importlib.util.spec_from_file_location('lab_graph_build',LAB/'graph/build.py');build=importlib.util.module_from_spec(spec);spec.loader.exec_module(build)
current_graph=load(LAB/'graph/generated/knowledge.json')
historic=[]
for folder in ['aoi-s2-jja-2025-2026-calibrated','aoi-s2-s1-jja-2025-2026-sigma']:
    manifest=load(ROOT/'runs'/folder/'run_manifest.json');rev=manifest['semantic_provenance']['knowledge_snapshot']['forest_cover_lab_revision']
    blob=subprocess.check_output(['git','show',rev+':graph/generated/knowledge.json'],cwd=LAB)
    graph=json.loads(blob);assert graph['revision']==manifest['semantic_provenance']['knowledge_snapshot']['graph_revision']
    build.validate_provenance(manifest,graph)
    historic.append({'run':folder,'historical_lab_commit':rev,'graph_revision':graph['revision'],
        'graph_blob_sha256':hashlib.sha256(blob).hexdigest(),'source':'local Git object, no checkout/fetch',
        'result':'PASS against its own historical graph; deliberately not re-pinned to current graph'})
dump('historical_provenance_checks.json',historic)
base=load(ROOT/'runs/aoi-s2-s1-jja-2025-2026-sigma/run_manifest.json')
round_record=yaml.safe_load((RD/'round.yaml').read_text())
manifest={k:deepcopy(base[k]) for k in ['aoi_id','geometry_hash','exchange_crs','area_method','forest_definition','parameters']}
manifest.update(run_id='road-like-ndvi-round-0002-audit-01-cache-reproduction',
    algorithm={'name':'Local reproduction of existing Sentinel screening decisions for audit','version':'audit-01-attempt-0001',
               'not_new_scientific_method':True,'not_full_production_pipeline_run':True},
    limitations=['All-land-cover screening; no forest baseline was consumed, despite later Hansen product selection.',
                 'Not monthly June generation, construction attribution, legality, held-out accuracy or causal validation.',
                 'The original 13 derived artifact hash mismatches remain preserved; original-manifest-matching source caches are required.',
                 'NumPy implements aggregation under the already-declared workflow divergence; no new Lab tool registration.',
                 'Private external instructions and exact serving model/client details are not captured.'])
manifest['parameters']['audit_scope']='Existing fixed/sigma/radar rules reproduced from local authenticated input assets only.'
manifest['data_provenance']=[{'dataset_name':name,'inventory_id':ds,'dataset_version':version,
    'source':'authenticated_inputs.json','evidence_role':'core estimation input','access_time_utc':datetime.now(timezone.utc).isoformat(),
    'notes':'Local reread; original URLs, scene acquisition and historical retrieval times remain in source_dates.json.'}
    for name,ds,version in [('Sentinel-2 L2A cached reflectance','DS-0002','archived Earth Search harmonized COGs'),
                           ('Sentinel-1 RTC cached linear intensity','DS-0003','archived Planetary Computer RTC')]]
sp=deepcopy(base['semantic_provenance']);sp['knowledge_snapshot']={
    'forest_cover_lab_revision':round_record['repos']['forest_cover_lab'],'graph_revision':current_graph['revision']}
nodes={n['id']:n for n in current_graph['nodes']}
for m in sp['methods']:m['version']=nodes[m['id']]['version']
sp['ai_planner_involved']=True;sp['planning_record_id']=round_record['graph']['approval']['planning_record_id']
sp['tools']=[{'id':'tool:rasterio','version':rasterio.__version__},{'id':'tool:pyproj','version':pyproj.__version__},
             {'id':'tool:shapely','version':shapely.__version__}]
manifest['semantic_provenance']=sp
manifest['observation_inventory']={'reference':'authenticated_inputs.json','sha256':sha(OUT/'authenticated_inputs.json')}
manifest['source_code_sha256']={f.relative_to(OUT).as_posix():sha(f) for f in (OUT/'scripts').glob('*.py')}
manifest['upstream_commits']=round_record['repos'];manifest['numpy_version']=np.__version__
manifest['outputs']=[{'path':f.relative_to(OUT).as_posix(),'artifact_type':'audit_reproduction','sha256':sha(f)}
                     for f in sorted((OUT/'recomputed').glob('*.tif'))]
jsonschema.Draft202012Validator(load(LAB/'validate/run_manifest.schema.json')).validate(manifest)
build.validate_provenance(manifest,current_graph)
dump('run_manifest.json',manifest)
dump('audit_run_checks.json',{'historical_manifest_provenance_at_own_pins':'PASS',
    'new_audit_manifest_schema':'PASS','new_audit_manifest_current_semantic_provenance':'PASS',
    'interpretation':'Schema/provenance and exact reproduction do not validate science.'})

claims=[]
def claim(id,proposition,status,evidence,limitations,roi='all'):
    claims.append({'id':id,'claim_id':id,'exact_proposition':proposition,'roi_id':roi,
        'period':'archived acquisitions / audit on 2026-10-24','status':status,'evidence_ids':evidence,
        'source_lineage':['local archived Sentinel/Copernicus','operator directions where stated'],
        'limitations':limitations})
claim('AUD-01','User identifies the two outlined corridors as the intended targets.','supported',
      ['operator_approval.txt','geometry_qa.json'],['User identification does not certify surveyed road edges or construction date.'],'ROI-01,ROI-02')
claim('AUD-02','Archived ROI/control coordinates are unchanged, valid and inside the AOI.','supported',
      ['roi_review.geojson','geometry_qa.json','inspect/ROI-01-compact.png','inspect/ROI-02-compact.png'],
      ['40 m sampling tolerance is not a measured registration error; controls remain visually selected.'])
claim('AUD-03','79 consumed raw assets match original run-manifest hashes.','supported',
      ['authenticated_inputs.json','cache_authentication.json'],['Byte authenticity is limited to the local archived chain, not independent provider certification.'])
claim('AUD-04','Thirteen original output-manifest mismatches are historical and remain excluded from original-manifest authority.','supported',
      ['cache_authentication.json','original_integrity.json','reproduction.json'],['Original expected bytes have not been restored; the immutable originals are not repaired.'])
claim('AUD-05','Existing production decisions reproduce exactly; optical change is absolute NDVI difference, not relative percent.','supported',
      ['reproduction.json','run_manifest.json'],['No threshold accuracy, cause or legal/forest claim follows.'])
claim('AUD-06','Two optical patches prefer zero integer shift; no correction applied.','supported',
      ['registration_qa.json'],['Subpixel, full-corridor and radar registration remain unverified.'])
claim('AUD-07','A verified before/after July-2025 orthophoto pair is available in the checked cache.','unresolved',
      ['orthophoto_date_audit.json'],['No linked flight date authenticates either side of the cutoff; no global availability search performed.'])
claim('AUD-08','An approved measured 2024 Hansen forest mask has been consumed.','not_tested',
      ['forest_baseline_audit.json'],['Product selection recorded; no local mask found/ingested. The 2024 edition is not itself measured 2024 canopy cover.'])
claim('AUD-09','Calendar-month June NDVI pairs and causal new-road conclusions are established.','not_tested',
      ['observation_dates.json'],['Only historical single-scene/summer decisions audited; monthly/causal analysis not authorized.'])
dump('findings.json',{'schema_version':'1.0','summary':'Local authentication/reproduction audit passed within its scope; scientific branch outputs and human acceptance remain pending.',
    'claims':claims,'stage_status':{'inspect':'audit-only complete with limitations','research':'not_run','corroborate':'not_run','report':'audit report only'},
    'limitations':manifest['limitations']})
dump('investigation.json',{'schema_version':'1.0','investigation_id':'road-like-ndvi-2025-2026-monthly-round-0002-audit-01',
    'updated_at_utc':datetime.now(timezone.utc).isoformat(),'repo_shas':round_record['repos'],'rois':'roi_review.geojson',
    'run_manifest_sha256':sha(OUT/'run_manifest.json'),'claims':claims,
    'sources':['authenticated_inputs.json','cache_authentication.json','source_dates.json','operator_approval.txt'],
    'artifacts':['audit_report.md','run_manifest.json','inspect/comparison.html','inspect/mask_contact_sheet.png'],
    'limitations':manifest['limitations'],'stages':{'audit':'completed; human acceptance pending','other_roles':'not_run'}})
text='''# audit-01: authenticated local-cache audit

Audit scope completed; scientific conclusions and output acceptance remain for human review. The round-0002 graph and this step alone were authorized. No remote access, downloads, paid external service, native subagent, later scientific role, baseline ingestion, public release or knowledge promotion occurred. Exact serving-model/client/billing details are not exposed; existing-session model billing is not claimed free.

## Geometry and user directions

The user confirms that the two outlined corridors are the intended targets. Their polygon coordinates and both controls are preserved byte-for-byte (SHA-256 b079d3dbff8a473daf6e3d33cdfdaedffc29de470425b8fe9a212f796a862125). All four geometries are valid and inside the AOI. Raw reference/target and outline figures were inspected, as were all four existing decision variants and both controls. The outlines follow the intended coarse corridors; they are sampling buffers, not surveyed road edges. No coordinates were moved or centreline invented. Control stability is not independently labeled.

The prior '*-native.png' files are explicitly generated from 20 m analytical crops in finish_review.py; filenames do not establish native 10 m evidence. All current audit crops are labeled 20 m. Multiple subpixel/road-edge claims remain outside this QA.

## Historical hash mismatch resolution

The calibrated optical manifest passes 59/59 output hashes. The sigma/radar manifest passes 213/226; the same 13 known derived/presentation mismatches persist. All 301 entries in the historical originals-before ledger and all 910 historical artifact-manifest entries still match. All 1,514 original run/review files match this audit's before/after fingerprints.

Resolution: preserve every original manifest and byte, exclude mismatching derivatives as evidence of the original manifest version, authenticate the 79 consumed local source assets against original output hashes, and regenerate the decisions in this audit with new checksums. This establishes a usable reproduced evidence chain without pretending the missing original expected bytes were recovered. Three current display masks also equal the reconstructed decisions on every pixel, despite two display-mask files differing in file hash; file-byte mismatch alone therefore does not imply a changed candidate array.

Historical provenance fails against today's graph because historical pins differ; each manifest PASSES against its own historical graph recovered from local Git (no fetch or checkout). The separate new audit run_manifest.json passes the current Lab run schema and semantic-provenance validator, with actual current pins and script/output checksums. None of these checks establishes scientific validity.

## Formulas, dates and calibration

NDVI=(NIR-Red)/(NIR+Red), calculated per SCL-screened observation. Archived change is **absolute current minus reference NDVI**, not relative percentage. Fixed optical: delta < -0.2 against the selected 15 June 2025 scene. Sigma optical: 20 June 2026 NDVI minus mean of eight selected summer-2025 dates < -2 population SD, with at least two valid references and positive SD. A single reference RGB scene does not depict that eight-date mean.

Reference dates are 14/15/30 June, 4/25 July and 4/14/26 August 2025. The selected full-AOI optical target is 20 June 2026. These are not full calendar-June means. The selected full-AOI inventory has only one June-2026 optical target; additional historical persistence crops are small windows, not full-corridor month support. This audit did not create monthly pairs.

Harmonized source reflectance uses scale .0001 with offset zero after the recorded BOA offset application; cached reflectance uses scale 1/offset 0. No second -0.1 offset was applied. Selected reference/target processing baselines are 05.11/05.12. SCL valid classes are 4,5,6,7; no dilation. Continuous source materialization uses bilinear resampling, SCL uses nearest; the audit rereads exact aligned 20 m caches. Missing evidence remains nodata.

Radar: ascending relative orbit 160, twelve selected acquisitions per summer, linear intensity transformed by 10log10 then temporal median in dB for both years. Candidates require deltaVV < -1.5 AND deltaVH < -1.0 dB. Combined masks are paired-valid AND, not calibrated probabilities or independent causal confirmation.

| Reproduced mask | Candidate pixels | Disagreeing values / validity |
|---|---:|---:|
| Fixed optical | 91,291 | 0 / 0 |
| Sigma optical | 121,242 | 0 / 0 |
| Radar | 119,603 | 0 / 0 |
| Sigma AND radar | 12,875 | 0 / 0 |

Fixed AND radar also reproduces 9,469 pixels in the current comparison mask. All eleven continuous raster/count comparisons pass 2e-6 tolerance, with maximum observed error 2.384185791015625e-7 and zero validity disagreements. These are audit reproducibility counts, not new forest-loss estimates.

## Registration and orthophoto cutoff

The two repeated 40x40 optical landmark tests both prefer [0,0] integer shift, with correlations 0.9420274456542702 and 0.7856362709960444. No shift was applied. This does not certify subpixel, full-corridor or SAR alignment.

The requested orthophoto rule is recorded: verified before-July-2025 images vs verified on/after-July-2025 images, and pre-cutoff only if no post-cutoff photo is available. The available cached 2025 layers conflict with generic 2023-06-09 metadata; neither is an authenticated acquisition date for the returned pixels. Other cached 2023/2024 windows lack usable imagery. No verified post-cutoff image is established in this cache, and availability elsewhere was not checked. Keep available imagery as undated physical context; relaxing the window does not resolve flight-to-image linkage. No construction interval follows.

## Hansen and later technical work

Hansen 2024 product selection is recorded as DS-0001, v1.12. No Hansen/treecover/lossyear mask was found in the checked Sentinel runs/data/configs directories, and none was downloaded. The Lab v1 contract uses treecover2000 and explicitly labels year-2000 baseline extent. It is not measured 2024 canopy cover. A remaining-cover proxy using annual loss needs an explicit reviewed temporal transformation and does not account for all regrowth. That contract decision stays outside this audit; no forest-specific estimates were made.

The archived sigma sample already selects unique optical calendar dates; generic monthly item counting still needs overlap/reprocessing protection. Choose explicit acquisition grouping and overlap/mosaic QA, preserve per-pixel membership, and test duplicate items before later monthly execution. Mask-dilation sensitivity needs a separate declared preprocessing parameter. A future deterministic reconciler should join claim/ROI/period with exact source hashes, retain conflicting statuses and shared lineage, and never vote an agent consensus into truth. A reviewed-evidence release adapter must verify all output links/hashes/licenses and human gates. These implementation choices are proposals, not execution of later graph nodes.

The current round's executed assignment remains unchanged. Any revised later-role harness or year-2024 temporal assumptions belong in a successor plan/round; no approval is inherited by discovery, quantification, corroboration, challenge or release.

## Evidence navigation

- [Source authentication](cache_authentication.json)
- [Exact reproduction](reproduction.json)
- [Geometry QA](geometry_qa.json) and [unchanged ROIs/controls](roi_review.geojson)
- [Offline per-ROI comparison](inspect/comparison.html)
- [Mask contact sheet](inspect/mask_contact_sheet.png)
- [Source dates and URLs](source_dates.json)
- [New audit run manifest](run_manifest.json)
- [Historical provenance checks](historical_provenance_checks.json)
- [Orthophoto date audit](orthophoto_date_audit.json)
- [Hansen contract/availability audit](forest_baseline_audit.json)

Disturbance candidates are not legal deforestation, confirmed forest state or causal loss labels. Hansen annual loss is not monthly ground truth. Sensor agreement does not establish cause.
'''
(OUT/'audit_report.md').write_text(text)
(OUT/'report').mkdir(exist_ok=True)
(OUT/'report/report.html').write_text(page('Audit report', '<h1>Local-cache audit only</h1><p><a href="../audit_report.md">Source report</a> · <a href="../inspect/comparison.html">Offline comparison</a></p><pre>'+__import__('html').escape(text)+'</pre>'))
print('Audit report and current-pinned derived-run manifest written; historical provenance checked at historical pins')
