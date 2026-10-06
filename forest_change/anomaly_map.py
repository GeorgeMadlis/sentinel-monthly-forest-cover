"""Real two-observation experiment, reusing the production Workflow stages."""
from pathlib import Path
import copy
import subprocess
import numpy as np
import rasterio
from rasterio.windows import Window
from .asset_access import AssetResolver
from .evidence import load, write_json, checksum, NON_CLAIMS
from .leaflet import prepare_overlays, generate_map, vendor_leaflet
from .pipeline import Workflow
from .providers import ObservationProvider, utc_now, validate_calibration_requirements
from .raster import read_asset, write_window
from .selection import rank_observations, rank_key


class SelectedProvider(ObservationProvider):
    def __init__(self, original, items, queries=None):
        self.original, self.items = original, items
        self.queries = queries or []

    def describe_source(self):
        return {**self.original.describe_source(), "discovery_mode": "selected-observation-view-of-archived-catalogue-query"}

    def search(self, geometry, start, end, filters):
        return sorted([i for i in self.items if start <= i['datetime'][:10] < end], key=lambda i:(i['datetime'],i['id']))

    def record_query(self, geometry, start, end, filters, items):
        result=super().record_query(geometry,start,end,filters,items)
        archived=next((q for q in self.queries if q['time_range']==[start,end]),None)
        if archived:
            result['query_timestamp']=archived['query_timestamp']
        result['query_kind']='selected-observation-view'
        return result


def run(manifest, aoi, output=None, access_policy='auto'):
    config=load(manifest)
    out=Path(output or config['output']['prefix']).resolve()
    out.mkdir(parents=True,exist_ok=True)
    write_json(out/'quality_settings.json',{'name':'ungated-anomaly-test','quality':{'require_min_observations_per_pixel':1}})
    workflow=Workflow(manifest,out/'quality_settings.json',aoi,str(out))
    if len(workflow.windows)!=1 or len(workflow.windows[0]['references'])!=1:
        raise ValueError('Map test requires one target window and one reference period')
    if set(workflow.config['observations']) != {'optical'} or workflow.config['observations']['optical']['features'] != ['NDVI'] or workflow.config['fusion']['mode'] != 'optical_only':
        raise ValueError('This two-image test requires NDVI optical-only configuration')
    original=workflow.providers['optical']
    resolver=AssetResolver(out/'cache',access_policy)
    periods={'reference':workflow.config['temporal']['reference_periods'][0], 'target':workflow.config['temporal']['target']}
    selected={}; queries=[]
    status={'run_id':config['run_id'],'started_at':utc_now(),'status':'running','periods':periods}
    write_json(out/'execution_status.json',status)
    try:
        for role,requested in periods.items():
            times=workflow.windows[0]['references'][0] if role=='reference' else workflow.windows[0]['target']
            print(f'Discovering {role}: {times}',flush=True)
            query_time=utc_now()
            filters=workflow.config['providers']['optical'].get('filters',{})
            items=original.search(workflow.geometry,*times,filters)
            if len(items)>workflow.config['execution']['max_observations_per_window']:
                raise ValueError('Catalogue observation cap exceeded')
            queries.append({**original.record_query(workflow.geometry,*times,filters,items),'query_timestamp':query_time,'geometry':workflow.geometry,'role':role})
            write_json(out/'catalogue_queries.json',{'queries':queries})
            print(f'Discovered {len(items)} {role} observations',flush=True)
            def progress(n,total,item):
                if n%10==0 or n==total:
                    print(f'Quality assessed {role}: {n}/{total} ({item})',flush=True)
            best,ranking=rank_observations(items,original,workflow.geometry,requested,resolver=resolver,progress=progress)
            validate_calibration_requirements(best['item'], workflow.config)
            write_json(out/(role+'_ranking.json'),ranking)
            selected[role]={'period':requested,**copy.deepcopy(best), 'selection_score':list(rank_key(best)),
                'rationale':'Descending AOI nondefective coverage, ascending AOI cloud/shadow, scene cloud, central-date distance, item ID; SCL assessed on 200 m equal-area grid', 'asset_access':{}}
            print(f'Selected {role}: {best["item"]["id"]} {best["metrics"]}',flush=True)
            # Materialize only derived AOI windows, never complete tiles unless resolver fallback requires them.
            for key,source in selected[role]['item']['assets'].items():
                resolved,decision=resolver.resolve(best['item'],key,source)
                win=Window(0,0,workflow.grid.width,workflow.grid.height)
                try:
                    values=read_asset(original,resolved,workflow.grid,win,categorical=key=='scl')
                except (OSError, rasterio.errors.RasterioError):
                    resolved,decision=resolver.resolve(best['item'],key,source,remote_failed=True)
                    values=read_asset(original,resolved,workflow.grid,win,categorical=key=='scl')
                clip=out/'source_windows'/role/(key+'.tif'); clip.parent.mkdir(parents=True,exist_ok=True)
                with rasterio.open(clip,'w',**workflow.grid.profile) as dst:
                    write_window(dst,values,win)
                selected[role]['asset_access'][key]={**decision,'derived_aoi_raster':str(clip.relative_to(out)),
                                                     'derived_sha256':checksum(clip)}
                selected[role]['item']['assets'][key]={'href':str(clip),'source_url':source['href'],
                    'asset_id':source.get('asset_id',key),'source_asset':source,'scale':1,'offset':0}
            write_json(out/'selected_observations.json',selected)
        write_json(out/'asset_access_decisions.json',list(resolver.records.values()))
        workflow.providers['optical']=SelectedProvider(original,[r['item'] for r in selected.values()],queries)
        workflow.run()
        metrics=complete_map(workflow,selected)
        status.update(status='completed',metrics=metrics,map='maps/anomaly_leaflet.html')
    except Exception as exc:
        status.update(status='failed',error_type=type(exc).__name__,error=str(exc))
        raise
    finally:
        if status['status'] != 'completed':
            status['finished_at']=utc_now()
            write_json(out/'execution_status.json',status)


def complete_map(workflow, selected):
    out=workflow.out
    config=workflow.config
    periods={r:v['period'] for r,v in selected.items()}
    maps=out/'maps'
    bounds=prepare_overlays(maps,workflow.geometry,selected,workflow.providers['optical'],workflow.path('w0000','disturbance'))
    # Vendor Leaflet runtime so file:// works offline with embedded analytical images.
    vendor_leaflet(maps)
    metadata={'run_id':config['run_id'],'periods':periods,'selected_items':{r:v['item']['id'] for r,v in selected.items()},
        'acquisitions':{r:v['item']['datetime'] for r,v in selected.items()}, 'provider':workflow.providers['optical'].describe_source(),
        'method':'NDVI target minus reference; one selected observation per period',
        'threshold':workflow.config['threshold'],'forest_mask':workflow.config['forest_mask'],
        'quality':'SCL classes 4,5,6,7; paired finite NDVI; bilinear continuous / nearest masks',
        'rgb':'B04/B03/B02 reflectance 0–0.3, gamma 2.2 on both dates', 'overlay_bounds':bounds,
        'selected_scene_quality':{r:v['metrics'] for r,v in selected.items()},
        'calibration':config['providers']['optical'].get('asset_calibration',{}),
        'non_claims':NON_CLAIMS}
    generate_map(maps/'anomaly_leaflet.html',workflow.geometry,bounds,selected,metadata)
    write_json(maps/'map_metadata.json',metadata)
    with rasterio.open(workflow.path('w0000','disturbance')) as src:
        values=src.read(1,masked=True)
        metrics={'anomaly_pixels':int(np.count_nonzero(values.filled(-9999)==1)),
                 'paired_valid_pixels':int(values.count()),'anomaly_ha':float(np.count_nonzero(values.filled(-9999)==1)*workflow.grid.pixel_ha)}
    write_json(out/'anomaly_metrics.json',metrics)
    status=load(out/'execution_status.json')
    status.update(status='completed',metrics=metrics,map='maps/anomaly_leaflet.html',finished_at=utc_now())
    write_json(out/'execution_status.json',status)
    workflow.manifest(workflow.inventory())
    evidence=load(out/'run_manifest.json')
    evidence.update(anomaly_map=metadata,source_assets={r:v['asset_access'] for r,v in selected.items()},
        artifacts={'leaflet_map':'maps/anomaly_leaflet.html','selected_observations':'selected_observations.json'},
        selection_policy={'type':'best-single-observation','assessment_resolution_m':200},metrics=metrics)
    repository=Path(__file__).resolve().parents[1]
    revision=subprocess.run(['git','rev-parse','HEAD'],cwd=repository,text=True,capture_output=True)
    evidence['code_provenance']={'base_commit':revision.stdout.strip() if revision.returncode==0 else None,
        'source_sha256':{str(p.relative_to(repository)):checksum(p) for p in sorted((repository/'forest_change').glob('*.py'))}}
    write_json(out/'run_manifest.json',evidence)
    print(f'Completed: {out}/maps/anomaly_leaflet.html; {metrics}',flush=True)
    return metrics
