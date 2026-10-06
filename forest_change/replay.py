"""Reprocess checksum-verified AOI windows after an explicit calibration review."""
import copy
from pathlib import Path
import shutil
import numpy as np
import rasterio
from rasterio.windows import Window
from .anomaly_map import SelectedProvider, complete_map
from .evidence import checksum, load, write_json, geometry_hash
from .pipeline import Workflow
from .providers import utc_now, validate_calibration_requirements
from .raster import write_window


def replay(manifest, aoi, previous_run, output=None):
    previous=Path(previous_run).resolve()
    config=load(manifest)
    out=Path(output or config['output']['prefix']).resolve()
    if out==previous or out.exists():
        raise ValueError('Replay requires a new output directory; prior evidence is preserved')
    out.mkdir(parents=True)
    selected=copy.deepcopy(load(previous/'selected_observations.json'))
    prior=load(previous/'run_manifest.json')
    queries=load(previous/'catalogue_queries.json')['queries']
    write_json(out/'quality_settings.json',load(previous/'quality_settings.json'))
    w=Workflow(manifest,out/'quality_settings.json',aoi,str(out))
    if geometry_hash(w.geometry) != geometry_hash(load(previous/'config_snapshot.json')['geometry']):
        raise ValueError('Replay AOI differs from archived source windows')
    status={'run_id':config['run_id'],'status':'running','started_at':utc_now(),
            'replay_from':str(previous),'discovery':'archived real STAC queries; no new catalogue query'}
    write_json(out/'execution_status.json',status)
    try:
        for role,record in selected.items():
            if record['period'] != (w.config['temporal']['target'] if role=='target' else w.config['temporal']['reference_periods'][0]):
                raise ValueError('Replay periods differ from archived selection')
            validate_calibration_requirements(record['item'],config)
            for key,asset in record['item']['assets'].items():
                previous_clip=previous/record['asset_access'][key]['derived_aoi_raster']
                previous_hash=record['asset_access'][key]['derived_sha256']
                if checksum(previous_clip)!=previous_hash:
                    raise ValueError('Archived source window checksum mismatch')
                source=asset['source_asset']
                metadata=source.get('raster:bands',[{}])[int(source.get('band',1))-1]
                original={k:source.get(k,metadata.get(k,default)) for k,default in [('scale',1),('offset',0)]}
                old=prior['parameters']['providers']['optical'].get('asset_calibration',{}).get(key,original)
                old={**original,**old}
                new=config['providers']['optical'].get('asset_calibration',{}).get(key,original)
                new={**original,**new}
                clip=out/'source_windows'/role/(key+'.tif');clip.parent.mkdir(parents=True,exist_ok=True)
                with rasterio.open(previous_clip) as src:
                    if (src.width,src.height,src.transform,str(src.crs))!=(w.grid.width,w.grid.height,w.grid.transform,w.grid.crs):
                        raise ValueError('Replay grid differs from archived windows')
                    values=src.read(1,masked=True).filled(np.nan)
                if key!='scl':
                    values=(values-float(old.get('offset',0)))/float(old.get('scale',1))*float(new.get('scale',1))+float(new.get('offset',0))
                with rasterio.open(clip,'w',**w.grid.profile) as dst:
                    write_window(dst,values,Window(0,0,w.grid.width,w.grid.height))
                asset['href']=str(clip)
                record['asset_access'][key].update(derived_aoi_raster=str(clip.relative_to(out)),derived_sha256=checksum(clip),
                    processing_access_mode='existing_derived_aoi_raster',calibration=new,
                    recalibration={'previous_raster':str(previous_clip),'previous_sha256':previous_hash,'previous_calibration':old,
                                   'method':'invert previous linear calibration, apply reviewed calibration; preserve nodata'})
        for name in ('catalogue_queries.json','reference_ranking.json','target_ranking.json'):
            shutil.copyfile(previous/name,out/name)
        write_json(out/'selected_observations.json',selected)
        write_json(out/'asset_access_decisions.json',[a for v in selected.values() for a in v['asset_access'].values()])
        w.providers['optical']=SelectedProvider(w.providers['optical'],[r['item'] for r in selected.values()],queries)
        w.run()
        maps=out/'maps';maps.mkdir()
        for filename in ('leaflet.js','leaflet.css'):
            shutil.copyfile(previous/'maps'/filename,maps/filename)
        shutil.copytree(previous/'maps/images',maps/'images')
        complete_map(w,selected)
        status=load(out/'execution_status.json')
    except Exception as exc:
        status.update(status='failed',error_type=type(exc).__name__,error=str(exc),finished_at=utc_now())
        write_json(out/'execution_status.json',status)
        raise
