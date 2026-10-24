from pathlib import Path
import copy, csv, hashlib, json, re, shutil, subprocess, sys
from datetime import datetime, timezone
import yaml
from shapely.geometry import shape

root=Path.cwd(); lab=root.parent/'forest-cover-lab'
base=root/'reviews/road-like-ndvi-2025-2026-monthly'; prior=base/'rounds/round-0001'; new=base/'rounds/round-0002'
if new.exists(): raise SystemExit('Successor already exists; reconcile without overwrite')
new.mkdir()
now=datetime.now(timezone.utc).isoformat()
sha=lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,d):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
def write(p,s):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s)
def status(p): return subprocess.check_output(['git','status','--porcelain=v1'],cwd=p,text=True)
def head(p): return subprocess.check_output(['git','rev-parse','HEAD'],cwd=p,text=True).strip()
archive=Path('/Users/server/projects/uploaded_artifacts/forest-cover-lab/forest-road-investigation-starter.zip')
starter=Path('/tmp/forest-road-bootstrap-starter/forest-road-investigation-starter')
for name in ['README.md','docs/BUNDLE_ARCHITECTURE.md','docs/SCIENTIFIC_PROTOCOL.md']:
 dst=base/'starter'/name; dst.parent.mkdir(parents=True,exist_ok=True)
 if dst.exists(): raise SystemExit('starter already copied')
 shutil.copyfile(starter/name,dst)
shutil.copytree(prior/'assignments',new/'assignments');shutil.copytree(prior/'roles',new/'roles')
record=yaml.safe_load((prior/'round.yaml').read_text());record['round_id']=record['round_id'].replace('round-0001','round-0002');record['created_utc']=now
record['graph']['approval']['planning_record_id']=record['graph']['approval']['planning_record_id'].replace('round-0001','round-0002')
record['graph']['approval']['proposed_by']='Codex local planning revision, 2026-10-23; predecessor round-0001 retained'
record['frame']['aoi_ref']='inputs/aoi.geojson; unchanged configs/aoi.example.geojson at Sentinel '+head(root)+'; ROIs: inputs/prior_rois.geojson copied unchanged from historical review, overlay QA pending'
for i in record['instances']:
 i['delegation']['permitted_writes']=[v.replace('round-0001','round-0002') for v in i['delegation']['permitted_writes']]
 p=new/i['assignment'];s=p.read_text().replace('round-0001','round-0002')
 s+='\n## Successor planning constraints\nPredecessor: round-0001, retained unchanged. This is a logical role plan, not proof of native delegation. Proposed hosts require availability checks; separate sessions need manual handoff. Null budgets are unspecified and require a bounded approval. Record actual model/runtime, prompt, loaded file SHA-256 values, exact commands, timestamps, source URLs/dates and limitations under schema 1.1 only after approval. No actual attempts are recorded in this bootstrap.\n'
 if i['id']=='audit-01':
  s=s.replace('Recreate existing signal on known reference/target scene IDs and compare byte/checksum where possible.','Recreate existing signal only from authenticated local cached scene windows and compare checksums where possible. No new downloads before the data-access freeze gate; missing or mismatched historical inputs are blockers.')
  s+='\nDo not reconstruct new centrelines from buffered polygon vertices. The archive contains two corridor polygons and two visual controls; source centreline recovery and overlay QA remain pending. Also write audit_evidence_manifest.json with original source paths, hashes and QA status.\n'
 if i['id']=='challenge-01':
  s=s.replace('Audit public-bundle map and narrative','Audit pre-assembly figures, map manifest and proposed narrative')
  s+='\nConsume primary_evidence_index.json, resolve original rasters/records by hash, and report inaccessible sources. The final assembled bundle is checked by the human release gate after assembly; do not require a future artifact before this role can start. Reconciled conclusions have been received, so report conclusion_exposure: received; this role is a challenge, not a blinded independent observation.\n'
 if i['id'] in ['eo-01','geo-01','works-01','literature-01']:
  s+='\nAlso produce '+i['id'].split('-')[0]+'_primary_evidence.json: a machine-readable list of source and derived artifact paths, SHA-256 values, acquisition/publication/retrieval dates, license, lineage and missing-input status. The reconciler must preserve these references for challenge and assembly. Shared providers do not establish independent source lineage.\n'
 if i['id']=='eo-01':
  s+='\nThe 10 m native optical grid is a visual/registration sensitivity only; the production area path rejects non-equal-area grids. Use a separate 10 m EPSG:6933 run for hectare sensitivity. No forest baseline is approved: stop forest-specific estimates, retain all-land-cover anomalies only. NDVI relative normalization is an investigation setting, not canonical Lab semantics.\n'
 p.write_text(s)
 for ref in i['harness_sources']:
  f=(new if ref['source']=='round' else lab)/ref['path_or_identifier'];ref['sha256']=sha(f)
  if ref['source']=='forest-cover-lab':ref['revision']=head(lab)
 nodes={n['id']:n for n in record['graph']['nodes']}
 nodes[i['id']]['step_plan']['plan_sha256']=sha(p)
 if i['id']=='audit-01': nodes[i['id']]['outputs'].append('audit_evidence_manifest.json')
 if i['id'] in ['eo-01','geo-01','works-01','literature-01']:
  nodes[i['id']]['outputs'].append(i['id'].split('-')[0]+'_primary_evidence.json')
 i['delegation']['output_contract']=', '.join(nodes[i['id']]['outputs'])
nodes={n['id']:n for n in record['graph']['nodes']}
# Explicit copies of edge carries avoid depending on YAML aliases.
for e in record['graph']['edges']:
 if e['from'] in ['audit-01','eo-01','geo-01','works-01','literature-01']:
  e['carries']=list(nodes[e['from']]['outputs'])
branch=[x for n in ['eo-01','geo-01','works-01','literature-01'] for x in nodes[n]['outputs']]
for e in record['graph']['edges']:
 if e['from']=='branch-gate':e['carries']=branch
nodes['reconcile']['outputs']+=['primary_evidence_index.json','map_manifest.json']
nodes['reconcile']['command']='PLANNED: implement scripts/reconcile_claims.py preserving hashed primary evidence references and map_manifest.json; not executed'
for e in record['graph']['edges']:
 if e['from']=='reconcile':e['carries']=list(nodes['reconcile']['outputs'])
 if e['from']=='decision-gate':e['carries']+=['primary_evidence_index.json','map_manifest.json']
nodes['assemble']['command']='PLANNED: reviewed-evidence release adapter required after decision-gate; existing scripts/build_bundle.py supports private planning drafts only'
write(new/'round.yaml',yaml.safe_dump(record,sort_keys=False,allow_unicode=True))
history=root/'reviews/20261006T174722Z-sentinel-road-investigation'
for src,dst in [(root/'configs/aoi.example.geojson',new/'inputs/aoi.geojson'),(history/'rois.geojson',new/'inputs/prior_rois.geojson')]:
 dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
write(new/'inputs/window_spec.yaml',yaml.safe_dump({'status':'proposed_pending_approval','timezone':'UTC','baseline':['2025-06-01','2025-07-01'],'target':['2026-06-01','2026-07-01'],'interval':'half-open','config_end_dates_inclusive':['2025-06-30','2026-06-30'],'aggregation':'mean of per-observation NDVI','minimum_valid_observations':3,'sensitivity_minimum':[2,5],'relative_domain_baseline_min':0.2,'relative_epsilon':0.1,'analysis_grid':{'crs':'EPSG:6933','resolution_m':20},'forest_mask':'not_approved'},sort_keys=False))
rois=json.loads((history/'rois.geojson').read_text());roirows=[]
for f in rois['features']:
 roirows.append({'id':f['properties']['id'],'role':f['properties']['role'],'bbox_wgs84_lonlat':list(shape(f['geometry']).bounds),'geometry_sha256':hashlib.sha256(json.dumps(f['geometry'],sort_keys=True,separators=(',',':')).encode()).hexdigest(),'qa':'not_tested','uncertainty':f['properties']['uncertainty']})
dump(new/'inputs/roi_locations.json',{'source':'reviews/20261006T174722Z-sentinel-road-investigation/rois.geojson','source_sha256':sha(history/'rois.geojson'),'features':roirows,'coordinate_policy':'Bounds are extracted from archived polygons, not reinterpretations or surveyed centrelines.'})
write(new/'planning_changes.md','''# Successor plan: round-0002

Predecessor round-0001 is preserved byte-for-byte from the starter overlay (canonical renders added separately). Both checkout commits and the graph match the starter pins. No upstream re-pin was necessary. Lab has pre-existing local edits, recorded in bootstrap/provenance.json; none were changed. Round 0002 exists because the proposed harness and artifact handoffs changed, not because an execution failed.

Changes: explicit audit/branch primary-evidence manifests; primary evidence index and map manifest forwarded through reconciliation, challenge and decision to assembly. The challenge audits pre-assembly evidence; final bundle review remains at release-gate, removing a future-artifact dependency. Audit recreation is cache-only before the freeze gate. Archived ROIs/controls and calendar windows now exist as local inputs. Native-grid visual QA is separated from equal-area area sensitivity. Assignment and selected-role SHA-256 values are recomputed. All approvals remain pending and every actual_executions list is empty.

Roles resolve (six standing, one round-only). Proposed chat/Claude hosts are manual handoffs with availability unverified; no native delegation is claimed. Null budgets are not authorization. The structural graph independence group forbids branch-to-branch paths; neutral discovery/ROI inputs are shared, and source independence still requires lineage review. Challenge receives conclusions and is not blinded.

Graph artifact labels are logical aliases. inputs/aoi.geojson, inputs/prior_rois.geojson and inputs/window_spec.yaml are present; audit/branch/reconcile outputs do not yet exist. Physical output paths will be artifacts/<instance-id>/<basename>, unless an approved read-only run reference is recorded with hashes. primary_evidence_index.json must carry exact paths/hashes, not just names. The reconciler and reviewed-evidence release adapter remain unimplemented and are blockers before those graph nodes execute. The separate private draft build is authorized bootstrap work, not an execution of the graph assemble node.

Before execution, freeze/commit the intended code and round inputs and use a new round pin if loaded repository instructions or implementation change. These commits identify today's baseline; they do not make uncommitted builder code part of that baseline. Capture exact bytes and dirty state. Do not edit executed harnesses.
''')
write(new/'monthly_pair_proposal.md','''# Minimal monthly-pair implementation proposal (not executed)

Existing Workflow.feature_stack computes calibrated, SCL-masked per-observation NDVI; composites uses its arithmetic mean when aggregation: mean. temporal.mode: monthly enforces matched full months; specify inclusive config end 2025-06-30 and 2026-06-30, yielding the protocol's half-open UTC windows. Use exactly one 2025 reference period and reference_statistic: period-composites. Both monthly means, per-pixel counts and absolute current-minus-reference change already exist. Set quality.require_min_observations_per_pixel: 3 in the quality/forest-definition input; no forest baseline is thereby implied. Set forest_mask: null, optical_only fusion and ungated anomaly evidence mode, with explicit all-land-cover labels. Run median and N=2/5 as distinct configurations/output prefixes.

Proposed small implementation diff:

- forest_change/algorithms.py: add a pure, configurable masked relative diagnostic delta/max(abs(reference),epsilon), only on common valid support with reference >= configured domain minimum; nodata remains NaN internally and -9999 on disk. Values are fractions; multiply by 100 only for a clearly labeled percentage display. Test near-zero, negative, missing and threshold boundaries.
- forest_change/pipeline.py: optionally export NDVI_relative_change and common_support alongside existing absolute rasters; retain independent monthly counts. Add compressed per-acquisition validity membership (ordered inventory IDs plus tiled/packed bitmaps) so each pixel's valid timestamps can be recovered; min/max timestamps alone do not meet the contract. Hash and include these outputs and calibration/mask/grid settings in the existing manifest. No change to candidate/fusion semantics.
- specs/workflow.schema.json and config.py: add opt-in diagnostics configuration with explicit epsilon/domain/min-count values; avoid new scientific IDs or hardcoded canonical thresholds. Keep legacy outputs compatible. Diagnostics follow run configuration, not a new Lab method. If semantic relationships change, propose them in Lab before implementation.
- Reporting: export common-support/unknown/relative-domain layers with distinct legends, RGB evidence dates, distributions and ROI denominators. Reuse local Leaflet assets; generic Workflow.report currently references a CDN and cannot meet this offline contract unmodified. Do not reuse anomaly_map's summer single-scene ranking as a monthly mean.

Validate with local synthetic unequal-clear-count observations that mean(NDVI) differs from NDVI(mean bands), full June boundaries, N=2/3/5 and median support, no-zero nodata, exact acquisition membership, calibration offsets and tiled equivalence. Reuse existing provider/calibration/grid tests. No real data are accessed by this proposal.

20 m EPSG:6933 is the primary area grid. For 10 m area sensitivity use EPSG:6933 separately. Native optical UTM can only support a separate visual/registration check; production must reject non-equal-area area calculations before raster allocation. No approved forest mask exists: forest-specific measurements are infeasible pending a baseline. SAR is ancillary and requires reviewed processing and orbit-matched dated acquisitions.
''')
write(new/'data_license_estimate.md','''# Local-only data and license estimate — not provider verification

No catalogue request, download, paid service, public repository or publication is authorized by this bootstrap. The estimates below are arithmetic planning scenarios, not live availability or price statements. Zero new acquisition cost/data transfer has been incurred here. Paid access budget: $0 unless separately approved. No upper transfer bound is approved yet; discovery must supply measured scene/block sizes before freeze-gate.

Archived grid: 2413 x 1351 = 3,259,963 cells; one float32 plane is 13,039,852 bytes (12.44 MiB) uncompressed. At a hypothetical 6–12 acquisitions per June, two years x red/NIR/SCL x 2 bytes x these cells is about 224–448 MiB of AOI samples. RGB adds roughly 149–298 MiB; SWIR1/2 about 149–298 MiB. Red/NIR/RGB are native 10 m; exact native-window transfer can be about four times the 20 m sample-volume scenario, plus overlapping tiles, remote COG block overfetch, masks and compression. SCL/native resolution differs. Reserve a provisional 2–10 GiB working envelope for June optical staging/derivatives; this is not a cap or measured requirement. July/August sensitivity roughly triples that envelope, and prior years/SAR/orthophotos require a separate estimate. Whole-scene downloads are outside this estimate. Per-pixel validity bitmaps can be far smaller than float timestamp planes. Six to twelve acquisitions is an assumption, not a claim that either June has adequate clear support.

Copernicus Sentinel, Earth Search/STAC, Estonian orthophotos/ETAK, official road/rail records and papers are proposed sources from the starter/archive, not newly verified. Dataset editions, exact licenses, attribution, provider terms, acquisition/flight dates, downloadable sizes, redistribution rights and any fees remain discovery outputs before data-access approval. A WMS label is not a flight date. The archive's 2025-layer/2023-flight conflict blocks temporal corroboration. S1 RTC access/processing and orbit compatibility are unverified.

Local archived PNGs used in the private draft carry original scene IDs/acquisition dates and hashes; their scientific authenticity and original manifest mismatches remain unresolved. Preserve Copernicus/Element 84 attribution. Leaflet 1.9.4 is vendored from existing local assets with copyright header; a complete redistribution license copy was not found locally, so verify/license before release. No claim that private draft status grants redistribution rights. Raw rasters are excluded.

../private-bundles is present locally with a .git directory (read-only existence check only); its remote identity, privacy, ownership and contents have not been verified. It was not used or modified. No new public-bundles checkout/repository was created. public-bundles remains a proposed human-approved curated release destination.
''')
# Curated local input snapshots: no raw rasters or provider calls.
files=[]
def curate(src,dst,label,extra=None):
 staging=new/'curated'/dst;staging.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,staging)
 e={'path':staging.relative_to(new).as_posix(),'destination':dst,'sha256':sha(src),'label':label,'provenance':str(src.relative_to(root)) if src.is_relative_to(root) else 'starter-package/'+src.name,'license':'not_verified_for_public_release','evidence_status':'archived_context_or_planning'}
 e.update(extra or {});files.append(e)
curate(new/'inputs/aoi.geojson','metadata/aoi.geojson','Pinned AOI')
curate(new/'inputs/prior_rois.geojson','metadata/rois.geojson','Archived polygons and controls unchanged')
for name in ['planning_changes.md','monthly_pair_proposal.md','data_license_estimate.md']:
 curate(new/name,'inquiry/'+name,name)
curate(new/'planning_changes.md','inquiry/round-0002.md','Pending decisions and unresolved evidence')
for name in ['SCIENTIFIC_PROTOCOL.md','BUNDLE_ARCHITECTURE.md']:
 curate(base/'starter/docs'/name,'metadata/'+name,'Starter document; subordinate to request and Lab contracts')
for name,header in [('claim_matrix.csv','claim_id,roi_id,period,status,evidence_ids,source_lineage,limitations\n'),('disagreements.csv','claim_id,conflict,status,limitations\n'),('sources.csv','source_id,producer,scene_id,acquisition_date,retrieval_date,license,lineage,status\n')]:
 write(new/'planning_tables'/name,header);curate(new/'planning_tables'/name,'metadata/'+name,'Empty planned table; no findings')
run=root/'runs/aoi-s2-jja-2025-2026-calibrated';selected=json.loads((run/'selected_observations.json').read_text())
h=(run/'maps/anomaly_leaflet.html').read_text();payload=json.loads(re.search(r'const d=(.*?);const map=',h)[1]);layers=[]
for role in ['reference','target']:
 item=selected[role]['item'];dst='figures/archived-'+role+'.png';label='Archived single scene '+item['datetime'][:10]+' (summer-ranked, NOT monthly mean)'
 curate(run/'maps'/(role+'.png'),dst,label,{'scene_id':item['id'],'acquisition_date':item['datetime'],'retrieval_date':'not_captured_in_bootstrap','provider':'Copernicus Sentinel-2 / Earth Search Element 84','lineage':'archived-calibrated-summer-scene','license':'original attribution retained; redistribution terms pending verification'})
 layers.append({'file':dst,'label':label,'bounds':payload['bounds']})
for name in ['leaflet.js','leaflet.css','images/layers.png','images/layers-2x.png','images/marker-icon.png','images/marker-icon-2x.png','images/marker-shadow.png']:
 curate(run/'maps'/name,'maps/'+name,'Locally cached Leaflet 1.9.4 vendor asset',{'license':'copyright header retained; full distribution license verification pending'})
# Graph assets are added to the spec only after the canonical renderer runs.
report='''# Road-like NDVI: private planned-only draft

No scientific role has run. All approvals remain pending. This draft validates packaging only.

Primary comparison proposed: [2025-06-01,2025-07-01) vs [2026-06-01,2026-07-01) UTC. June must be explicitly approved. Mean per-observation NDVI; N>=3 in both months; median and N=2/5 sensitivity. Relative domain baseline>=0.2, epsilon=0.1, run-specific configuration.

The two images are archived single acquisitions on 15 June 2025 and 20 June 2026 selected from summer windows, NOT full-month composites. The viewer overlays the exact prior polygons and controls. ROI identities, surveyed centrelines and overlay QA remain unresolved. The archive reports pre-existing hash mismatches and an unresolved 2025-layer/2023-flight orthophoto conflict; no new conclusion is inferred. Missing layers, baseline mask and measured temporal support remain absent.

Read the seven per-role plans, canonical graph, planning_changes, monthly_pair_proposal and data_license_estimate. Reconciliation and release adapter implementation remain future work. No forest-specific or construction-date claim is made. Public release and knowledge promotion require separate human reviews.

ROI bounds (WGS84 longitude,latitude; extracted mechanically, not surveyed):
'''
for r in roirows:report+='\n'+r['id']+': '+str(r['bbox_wgs84_lonlat'])+'; '+r['uncertainty']+'\n'
spec={'status':'private_planned_draft','metadata':{'forest_definition_status':'not_approved','forest_mask_status':'absent','available_labels':[],'license_status':'pending_source_verification_no_public_release','evidence_status':'planned_only_with_archived_single_scene_context','source_date_status':'scene dates from archived inventory; orthophoto date contradiction unresolved'},'report_markdown':report,'map_layers':layers,'unavailable_layers':['2025/2026 June monthly means','absolute and relative monthly NDVI','monthly candidate masks','verified road/rail geometries','independently dated orthophoto pair','approved forest baseline'],'files':files}
dump(new/'bundle_spec.json',spec)
# Read and fingerprint the selected instructions/scripts without claiming specialist execution.
loaded=[root/p for p in ['AGENTS.md','README.md','docs/architecture.md','workflow.yaml','specs/monthly_forest_loss_spec.md','docs/agent_harness.md']]
loaded += [lab/p for p in ['AGENTS.md','docs/agents.md','agent_harness/README.md','agent_harness/schemas/round.schema.json','agent_harness/scripts/validate_round.py','agent_harness/scripts/round_graph.py','agent_harness/scripts/render_round_graph.py','graph/README.md','graph/build.py','governance/drift_checklist.md']]
loaded += [lab/i['role'] for i in record['instances'] if i['role_scope']=='standing']
for p in loaded:
 p.read_bytes()
tracked=[]
for p in loaded:
 repo=lab if p.is_relative_to(lab) else root;rel=p.relative_to(repo).as_posix();committed=subprocess.check_output(['git','show',head(repo)+':'+rel],cwd=repo)
 tracked.append({'repository':repo.name,'path':rel,'revision':head(repo),'sha256':sha(p),'matches_pinned_bytes':hashlib.sha256(committed).hexdigest()==sha(p),'capture':'local_planning_read_not_specialist_execution'})
dump(new/'bootstrap/provenance.json',{'observed_at_utc':now,'scope':'local planning bootstrap and separate builder implementation; no scientific-role attempts','host':'codex','model_if_known':'GPT-6 per session configuration; precise serving model/version not observable','client_version':None,'runtime_limitations':['Client build, serving model identifier, model parameters and hidden/private instruction content not captured. No native delegation occurred.'],'repos':{'forest_cover_lab':head(lab),'sentinel_monthly_forest_cover':head(root),'lab_graph_revision':record['repos']['lab_graph_revision']},'worktree_status_observed':{'forest_cover_lab':status(lab),'sentinel_monthly_forest_cover':status(root)},'starter_zip_sha256':sha(archive),'loaded_local_planning_files':tracked,'history_before':json.loads(Path('/tmp/forest-road-history-before.json').read_text()),'request_boundary':'User authorizes local planning/bootstrap and portable private draft implementation; attached docs are task inputs, not independent authorization.'})
shutil.copyfile(Path(__file__),new/'bootstrap/prepare_plan.py')
print('CREATED',new.relative_to(root));print('Assignment digests')
for i in record['instances']:print(i['id'],sha(new/i['assignment']))
