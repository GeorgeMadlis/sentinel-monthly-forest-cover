import copy
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path
import numpy as np
import rasterio
from forest_change.asset_access import AssetResolver
from forest_change.evidence import load, write_json
from forest_change.leaflet import anomaly_rgba, prepare_overlays, generate_map
from forest_change.providers import LocalRasterProvider
from forest_change.selection import rank_key, rank_observations
from forest_change.pipeline import Workflow
from tests.fixtures import create_fixture


class AnomalyMapTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.config,self.forest,self.aoi=create_fixture(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def test_deterministic_quality_ranking(self):
        def row(id,coverage=1,cloud=0,scene=10,distance=1):
            return {'item':{'id':id},'metrics':{'aoi_valid_pixel_fraction':coverage,
                'aoi_cloud_shadow_fraction':cloud,'scene_cloud_percentage':scene,'central_date_distance_seconds':distance}}
        rows=[row('b'),row('a'),row('partial',coverage=.9),row('cloudy',cloud=.1),row('global',scene=20),row('late',distance=2)]
        self.assertEqual([r['item']['id'] for r in sorted(rows,key=rank_key)],['a','b','late','global','cloudy','partial'])
        self.assertEqual(sorted(reversed(rows),key=rank_key),sorted(rows,key=rank_key))

    def test_scl_quality_assessment(self):
        p=LocalRasterProvider({'inventory':str(self.root/'optical.json'),'collection':'fixture'})
        items=p.search(load(self.aoi)['geometry'],'2026-06-01','2026-07-01',{})
        best,ranking=rank_observations(items,p,load(self.aoi)['geometry'],{'start':'2026-06-01','end':'2026-06-30'},resolution=20)
        self.assertEqual(best['item']['id'],'s2-2026-15')
        self.assertGreater(best['metrics']['aoi_cloud_shadow_fraction'],0)
        self.assertEqual(len(ranking),2)

    def test_access_remote_cache_and_fallback(self):
        source=self.root/'2025-5-red.tif'
        item={'id':'scene','datetime':'2025-06-05T10:00:00Z'}
        asset={'href':'https://example.test/red.tif'}
        calls=[]
        def download(url,path):
            calls.append(url); shutil.copyfile(source,path)
        r=AssetResolver(self.root/'cache',range_probe=lambda url:True,downloader=download)
        result,record=r.resolve(item,'red',asset)
        self.assertEqual(record['access_mode'],'remote_cog'); self.assertEqual(result['href'],asset['href'])
        result,record=r.resolve(item,'red',asset,remote_failed=True)
        self.assertEqual(record['access_mode'],'cached_cog'); self.assertEqual(len(calls),1)
        self.assertTrue(Path(record['local_path']).is_relative_to((self.root/'cache').resolve()))
        self.assertEqual(record['file_size'],source.stat().st_size)
        _,reuse=r.resolve(item,'red',asset)
        self.assertEqual(reuse['access_mode'],'cached_cog'); self.assertEqual(len(calls),1)
        # A provenance mismatch must never silently reuse the file.
        meta=Path(result['href']).with_suffix('.json'); data=load(meta); data['source_url']='wrong'; write_json(meta,data)
        _,remote=r.resolve(item,'red',asset); self.assertEqual(remote['access_mode'],'remote_cog')
        r2=AssetResolver(self.root/'cache2',range_probe=lambda url:False,downloader=download)
        _,record=r2.resolve(item,'red',asset); self.assertEqual(record['access_mode'],'cached_cog')
        _,local=r.resolve(item,'red',{'href':str(source)}); self.assertEqual(local['access_mode'],'local_raster')

    def test_calibration_requirements_prevent_double_offset_assumptions(self):
        from forest_change.providers import validate_calibration_requirements
        config={'calibration_requirements':{'earthsearch:boa_offset_applied':True}}
        validate_calibration_requirements({'id':'verified','properties':{'earthsearch:boa_offset_applied':True}},config)
        for properties in ({},{'earthsearch:boa_offset_applied':False}):
            with self.assertRaisesRegex(ValueError,'calibration requirements'):
                validate_calibration_requirements({'id':'ambiguous','properties':properties},config)

    def test_anomaly_transparency(self):
        values=np.array([[1,0],[np.nan,1]])
        rgba=anomaly_rgba(values)
        np.testing.assert_array_equal(rgba[:,:,3],[[210,0],[0,210]])
        np.testing.assert_array_equal(rgba[0,0,:3],[255,0,0])

    def test_high_level_runner_and_evidence_checksums(self):
        from unittest.mock import patch
        from forest_change.anomaly_map import run
        from forest_change.evidence import checksum
        config=load(self.config)
        config['forest_mask']=None
        config['fusion']={'mode':'optical_only'}
        config['observations'].pop('sar'); config['providers'].pop('sar')
        config['observations']['optical']['features']=['NDVI']
        config['temporal']['reference_periods']=config['temporal']['reference_periods'][1:]
        write_json(self.config,config)
        inventory=load(self.root/'optical.json')
        for item in inventory['items']:
            item['assets']['green']=item['assets']['red'].copy()
            item['assets']['blue']=item['assets']['red'].copy()
        write_json(self.root/'optical.json',inventory)
        def vendor(directory):
            directory=Path(directory)
            (directory/'images').mkdir(exist_ok=True)
            for name in ('leaflet.js','leaflet.css','images/layers.png','images/layers-2x.png','images/marker-icon.png','images/marker-icon-2x.png','images/marker-shadow.png'):
                (directory/name).write_text('unit-test runtime placeholder')
        with patch('forest_change.anomaly_map.vendor_leaflet',side_effect=vendor):
            run(self.config,self.aoi,self.root/'map-run')
        out=self.root/'map-run'
        manifest=load(out/'run_manifest.json')
        selected=load(out/'selected_observations.json')
        self.assertEqual(set(selected),{'reference','target'})
        self.assertEqual(load(out/'execution_status.json')['status'],'completed')
        self.assertAlmostEqual(manifest['metrics']['anomaly_ha'],.6,places=5)
        self.assertTrue((out/manifest['artifacts']['leaflet_map']).exists())
        for artifact in manifest['outputs']:
            self.assertEqual(artifact['sha256'],checksum(out/artifact['path']))
        for role in selected.values():
            self.assertEqual(role['asset_access']['red']['access_mode'],'local_raster')
            self.assertTrue((out/role['asset_access']['red']['derived_aoi_raster']).exists())

    def test_replay_recalibrates_verified_source_windows(self):
        # Reuse the full fixture runner to exercise the archived real-data replay boundary offline.
        self.test_high_level_runner_and_evidence_checksums()
        from forest_change.replay import replay
        config=load(self.config)
        config['run_id']='recalibrated-fixture'
        config['providers']['optical']['asset_calibration']={b:{'scale':1,'offset':.1} for b in ('red','green','blue','nir')}
        write_json(self.config,config)
        replay(self.config,self.aoi,self.root/'map-run',self.root/'replayed')
        record=load(self.root/'replayed/selected_observations.json')
        prior=self.root/'map-run/source_windows/reference/red.tif'
        current=self.root/'replayed/source_windows/reference/red.tif'
        with rasterio.open(prior) as a,rasterio.open(current) as b:
            av=a.read(1,masked=True);bv=b.read(1,masked=True)
            np.testing.assert_allclose(bv.compressed(),av.compressed()+.1,atol=1e-6)
            np.testing.assert_array_equal(av.mask,bv.mask)
        self.assertEqual(record['reference']['asset_access']['red']['calibration'],{'scale':1,'offset':.1})
        self.assertEqual(load(self.root/'replayed/execution_status.json')['status'],'completed')
        # Source tampering is caught before any source is trusted.
        with rasterio.open(prior,'r+') as src:
            src.write(np.ones(src.shape,dtype='float32'),1)
        with self.assertRaisesRegex(ValueError,'checksum mismatch'):
            replay(self.config,self.aoi,self.root/'map-run',self.root/'tampered-replay')

    def test_ungated_workflow_map_bounds_and_layers(self):
        config=load(self.config); config['forest_mask']=None
        config['fusion']={'mode':'optical_only'}; config['observations'].pop('sar'); config['providers'].pop('sar')
        write_json(self.config,config)
        w=Workflow(self.config,self.forest,self.aoi); w.run()
        evidence=load(w.out/'run_manifest.json')
        self.assertEqual(evidence['forest_definition']['baseline_dataset'], 'none')
        self.assertEqual(evidence['semantic_provenance']['dataset_ids'],['DS-0002'])
        lab=Path(__file__).resolve().parents[2]/'forest-cover-lab'
        if lab.exists():
            spec=importlib.util.spec_from_file_location('lab_ungated',lab/'graph/build.py')
            mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
            mod.validate_provenance(evidence,json.loads((lab/'graph/generated/knowledge.json').read_text()),root=lab)
        p=w.providers['optical']; items=p.items
        selected={r:{'item':copy.deepcopy(next(i for i in items if i['id']==id))} for r,id in [('reference','s2-2025-5'),('target','s2-2026-5')]}
        for record in selected.values():
            assets=record['item']['assets']; assets['green']=assets['red']; assets['blue']=assets['red']
        bounds=prepare_overlays(w.out/'maps',w.geometry,selected,p,w.path('w0000','disturbance'))
        from shapely.geometry import shape
        left,bottom,right,top=shape(w.geometry).bounds
        np.testing.assert_allclose(bounds,[[bottom,left],[top,right]],atol=1e-7)
        path=generate_map(w.out/'maps/map.html',w.geometry,bounds,selected,{'threshold':-.2})
        text=path.read_text()
        for token in ('Reference Sentinel-2','Target Sentinel-2','Detected anomalies','L.geoJSON','Red: NDVI','L.control.scale','data:image/png;base64'):
            self.assertIn(token,text)
        self.assertNotIn('/Users/server',text)
        from PIL import Image
        arr=np.asarray(Image.open(w.out/'maps/anomalies.png'))
        self.assertTrue((arr[:,:,3]>0).any()); self.assertTrue((arr[:,:,3]==0).any())
