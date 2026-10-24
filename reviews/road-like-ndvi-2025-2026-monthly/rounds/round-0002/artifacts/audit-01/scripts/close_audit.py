"""Finalize this observed sequential-role attempt; leave every later approval pending."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import yaml

OUT=Path(__file__).resolve().parents[1];ROOT=OUT.parents[5];RD=OUT.parents[1];LAB=ROOT.parent/'forest-cover-lab'
PYTHON=str(ROOT/'.venv/bin/python')
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def load(p):return json.loads(p.read_text())
def dump(p,d):p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')

before=load(OUT/'originals_before.json')
changed=[name for name,expected in before.items() if sha(ROOT/name)!=expected]
assert not changed,'Original evidence changed'
elapsed=(datetime.now(timezone.utc)-datetime.fromisoformat('2026-10-24T06:40:17+00:00')).total_seconds()
assert elapsed<1800,'Stop: audit wall-time budget exhausted'
dump(OUT/'execution_observations.json',{
    'host':'codex','delegation_mode':'sequential_role','native_subagent':False,
    'context':'inherited planning conversation','client_version':None,'serving_model':None,
    'model_configuration':{},'remote_access_used':False,'external_paid_services_used':False,
    'billing_limitation':'Existing hosted model-session billing is not visible; no claim that this session is free.',
    'budget':{'tool_call_limit':80,'elapsed_seconds_limit':1800,'tracking':'Manual count; preflight and orchestrator calls counted conservatively. No runtime-enforced counter available.'},
    'elapsed_seconds_at_integrity_check':elapsed,'originals_unchanged':len(before),
    'visual_review':['ROI-01 raw/outline pair','ROI-02 raw/outline pair','both controls','four reproduced decision variants in mask contact sheet'],
    'browser_test':'not_performed_in_this_audit; supported local image tools used and static HTML links checked',
    'limitations':['Exact serving model/client/private instructions are not captured.','Exploratory preflight reads have no complete retained shell transcript; executed scripts and main command logs are captured.']})

def inventory():
    manifest=load(OUT/'audit_evidence_manifest.json');manifest['files']=[]
    for p in sorted(OUT.rglob('*')):
        if p.is_file() and '_html' not in p.parts and p.name not in ['audit_evidence_manifest.json','index.html']:
            manifest['files'].append({'path':p.relative_to(OUT).as_posix(),'size_bytes':p.stat().st_size,'sha256':sha(p)})
    dump(OUT/'audit_evidence_manifest.json',manifest)

argv=[PYTHON,str(ROOT/'scripts/build_review_site.py'),str(OUT),'--strict']
inventory();start=datetime.now(timezone.utc).isoformat()
p=subprocess.run(argv,cwd=ROOT,text=True,capture_output=True)
assert p.returncode==0,p.stdout+p.stderr
dump(OUT/'review_site_check.json',{'argv':argv,'started_utc':start,'ended_utc':datetime.now(timezone.utc).isoformat(),
    'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'scope':'HTML/Markdown/local paths, not science'})
inventory()
# Second build includes the observed check record and its final manifest hash.
p=subprocess.run(argv,cwd=ROOT,text=True,capture_output=True)
assert p.returncode==0,p.stdout+p.stderr
print(p.stdout.strip(),flush=True)

d=yaml.safe_load((RD/'round.yaml').read_text());instance=next(i for i in d['instances'] if i['id']=='audit-01')
attempt=instance['actual_executions'][-1]
assert attempt['status']=='running'
existing={(r['source'],r['path_or_identifier']) for r in attempt['loaded_harness']}
for ref in load(OUT/'additional_loaded_files.json'):
    if (ref['source'],ref['path_or_identifier']) not in existing:attempt['loaded_harness'].append(ref)
for file in sorted((OUT/'scripts').glob('*.py')):
    attempt['loaded_harness'].append({'source':'round','path_or_identifier':file.relative_to(RD).as_posix(),
        'revision':None,'sha256':sha(file),'capture_status':'captured'})
source_assets=load(OUT/'authenticated_inputs.json')['assets']
source_refs=sorted({a['source'] for a in source_assets})
source_refs+=['sentinel-local:reviews/20261006T174722Z-sentinel-road-investigation/rois.geojson',
              'artifacts/audit-01/operator_approval.txt','artifacts/audit-01/source_dates.json']
attempt['source_refs']=source_refs;attempt['independence']['evidence_inspected']=source_refs
attempt['handoffs']=[{'source':'archived-review','path_or_identifier':'reviews/20261006T174722Z-sentinel-road-investigation/rois.geojson',
    'revision':None,'sha256':sha(OUT/'roi_review.geojson'),'capture_status':'captured'},
    {'source':'round','path_or_identifier':'artifacts/audit-01/operator_approval.txt','revision':None,
     'sha256':sha(OUT/'operator_approval.txt'),'capture_status':'captured'}]
attempt['coordination_events'].append({'kind':'reconciliation',
    'detail':'Preserved 13 historical mismatches, authenticated raw caches, reproduced production decisions, checked historical manifests at their own local Git graph pins; no scientific promotion.',
    'artifact':{'source':'round','path_or_identifier':'artifacts/audit-01/cache_authentication.json',
                'revision':None,'sha256':sha(OUT/'cache_authentication.json'),'capture_status':'captured'}})
files=[p for p in sorted(OUT.rglob('*')) if p.is_file() and '__pycache__' not in p.parts]
attempt['output_refs']=[p.relative_to(RD).as_posix() for p in files]
attempt['output_hashes']={p.relative_to(RD).as_posix():sha(p) for p in files}
attempt['checks']=['79 raw source assets original-manifest authenticated; 59/59 optical and 213/226 sigma-run output hashes match.',
    '301/301 historical-original hashes and 910/910 historical artifact hashes match.',
    '1514/1514 original run/review files unchanged before/after audit.',
    '11 continuous raster/count comparisons <=2e-6 and zero validity disagreements; all four production masks exactly reproduced.',
    'Four valid unchanged ROI/control polygons inside AOI; two optical integer-shift landmark checks prefer zero.',
    'Historical semantic provenance passes against historical locally available graph; new audit run schema/current semantic provenance pass.',
    'Portable review site --strict passes with zero link problems; no browser runtime test in this audit.',
    'Audit acceptance is limited to source/code/geometry/reproduction QA; human output acceptance pending.']
attempt['limitations']+=['Hansen 2024 product choice is not an approved measured 2024 canopy mask; no baseline consumed.',
    'Orthophoto flight-to-pixel dates remain unresolved under either interpretation of the July boundary.',
    'No surveyed road-edge, subpixel/full-corridor or radar-registration certification; controls have no independent stability label.',
    'No monthly June pair, dedup/dilation implementation, later role execution, download, publication or promotion.',
    'Approval file is a normalized transcription of the user message; original transport timestamp/format not exposed.']
attempt['ended_utc']=datetime.now(timezone.utc).isoformat();attempt['status']='completed';instance['selection_status']='completed'
assert (datetime.fromisoformat(attempt['ended_utc'])-datetime.fromisoformat('2026-10-24T06:40:17+00:00')).total_seconds()<1800
assert all(not i['actual_executions'] for i in d['instances'] if i['id']!='audit-01')
(RD/'round.yaml').write_text(yaml.safe_dump(d,sort_keys=False,allow_unicode=True))
for args in [[PYTHON,str(LAB/'agent_harness/scripts/validate_round.py'),str(RD/'round.yaml'),'--lab',str(LAB)],
             [PYTHON,str(LAB/'agent_harness/scripts/render_round_graph.py'),str(RD/'round.yaml'),'--lab',str(LAB)],
             [PYTHON,str(LAB/'agent_harness/scripts/render_round_graph.py'),str(RD/'round.yaml'),'--lab',str(LAB),'--check']]:
    p=subprocess.run(args,cwd=ROOT,text=True,capture_output=True)
    print(p.stdout.strip(),flush=True)
    if p.returncode:raise RuntimeError(p.stderr+p.stdout)
print('AUDIT COMPLETED; later steps/gates remain pending; elapsed seconds including preflight',round((datetime.now(timezone.utc)-datetime.fromisoformat('2026-10-24T06:40:17+00:00')).total_seconds(),1))
