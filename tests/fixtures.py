"""Tiny deterministic local Sentinel-like rasters; not real satellite evidence."""
from pathlib import Path
import numpy as np
import rasterio
from affine import Affine
from rasterio.warp import transform_geom
from shapely.geometry import box, mapping
import yaml

from forest_change.evidence import write_json


def create_fixture(root):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    transform = Affine(20, 0, 2300000, 0, -20, 6000000)
    geom = transform_geom('EPSG:6933', 'EPSG:4326', mapping(box(2300000, 5999800, 2300200, 6000000)))
    write_json(root/'aoi.geojson', {'type':'Feature', 'geometry':geom, 'properties':{}})
    def raster(name, values):
        with rasterio.open(root/name, 'w', driver='GTiff', width=10, height=10, count=1, dtype='float32', crs='EPSG:6933', transform=transform, nodata=-9999) as dst:
            dst.write(values.astype('float32'), 1)
        return {'href':name, 'band':1}
    forest = np.ones((10,10)); forest[3,3] = 0
    raster('forest.tif', forest)
    props = {'sat:orbit_state':'ascending','sat:relative_orbit':42,'sar:instrument_mode':'IW','sar:polarizations':['VV','VH']}
    optical, sar = [], []
    for year in (2024,2025,2026):
        for day in (5,15):
            tag = f'{year}-{day}'
            bands = {'red':np.full((10,10),.2), 'nir':np.full((10,10),.8), 'swir1':np.full((10,10),.3), 'swir2':np.full((10,10),.4), 'scl':np.full((10,10),4)}
            vv, vh = np.full((10,10),-10.), np.full((10,10),-16.)
            if year == 2026:
                bands['red'][2:6,2:6] = .8; bands['nir'][2:6,2:6] = .2
                bands['scl'][2,2] = 9
                vv[4:8,4:8] -= 3; vh[4:8,4:8] -= 3
            optical.append({'id':f's2-{tag}', 'datetime':f'{year}-06-{day:02d}T10:00:00Z', 'geometry':geom, 'properties':{}, 'assets':{b:raster(f'{tag}-{b}.tif',v) for b,v in bands.items()}})
            sar.append({'id':f's1-{tag}', 'datetime':f'{year}-06-{day:02d}T10:00:00Z', 'geometry':geom, 'properties':props, 'assets':{'VV':raster(f'{tag}-vv.tif',vv), 'VH':raster(f'{tag}-vh.tif',vh)}})
    write_json(root/'optical.json', {'items':optical}); write_json(root/'sar.json', {'items':sar})
    config = {'schema_version':'2.0','run_id':'synthetic', 'aoi_id':'synthetic-aoi', 'application':'seasonal-forest-change',
              'observations':{'optical':{'dataset':'DS-0002', 'version':'synthetic-1', 'features':['NDVI','NDMI','NBR'], 'quality':{'mode':'scl', 'valid_classes':[4,5,6,7]}},
                              'sar':{'dataset':'DS-0003','version':'synthetic-1', 'features':['VV','VH','VV_MINUS_VH_DB'], 'units':'db', 'aggregation':'mean',
                                     'thresholds':{'VV':-1.5,'VH':-1, 'VV_MINUS_VH_DB':1},
                                     'preprocessing':{'orbit_direction':'ascending','relative_orbit':42,'instrument_mode':'IW','terrain_flattening':'not-applied-synthetic','speckle_treatment':'not-applied-synthetic'}}},
              'providers':{'optical':{'type':'local','inventory':'optical.json','collection':'synthetic-s2'}, 'sar':{'type':'local','inventory':'sar.json','collection':'synthetic-s1'}},
              'temporal':{'mode':'matched-season','alignment':'calendar-date','target':{'start':'2026-06-01','end':'2026-06-30'},'reference_periods':[{'start':'2024-06-01','end':'2024-06-30'},{'start':'2025-06-01','end':'2025-06-30'}],'aggregation':'median','reference_statistic':'period-composites'},
              'execution':{'backend':'local-python','crs':'EPSG:6933','resolution':20,'tile_size':4,'max_observations_per_window':256},
              'forest_mask':{'path':'forest.tif','dataset':'DS-0001','version':'synthetic-1','reference_year':2025,'threshold':1,'transformation':'threshold-gte'},
              'threshold':{'mode':'fixed','value':-.2,'min_component_pixels':1,'min_valid_pixel_ratio':0}, 'fusion':{'mode':'optical_and_sar'},
              'output':{'prefix':str(root/'output'), 'export_quicklooks':True}}
    (root/'workflow.yaml').write_text(yaml.safe_dump(config))
    (root/'forest.yaml').write_text(yaml.safe_dump({'name':'synthetic external baseline','quality':{'require_min_observations_per_pixel':2}}))
    return root/'workflow.yaml', root/'forest.yaml', root/'aoi.geojson'
