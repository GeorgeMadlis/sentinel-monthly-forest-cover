from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock

import numpy as np
import rasterio
import yaml
from affine import Affine
from jsonschema import Draft202012Validator, ValidationError
from rasterio.windows import Window

from forest_change.algorithms import aggregate, clean, feature, fuse, normalized_difference
from forest_change.config import normalize, read_config
from forest_change.evidence import load, write_json
from forest_change.pipeline import Workflow
from forest_change.providers import LocalRasterProvider, ObservationProvider, STACProvider
from forest_change.raster import Grid, read_asset, tiles
from forest_change.semantics import explain
from forest_change.temporal import windows
from tests.fixtures import create_fixture

ROOT = Path(__file__).resolve().parents[1]


class AlgorithmTests(unittest.TestCase):
    def test_features_and_provider_independence(self):
        red, nir = np.array([.2,0,np.nan], dtype='float32'), np.array([.8,0,.5], dtype='float32')
        np.testing.assert_allclose(normalized_difference(nir,red), [.6,np.nan,np.nan], equal_nan=True)
        bands = {'nir':nir,'red':red,'swir1':red,'swir2':red,'VV':np.array([-10.]),'VH':np.array([-16.])}
        for f in ('NDVI','NDMI','NBR'):
            np.testing.assert_allclose(feature(f,bands), [.6,np.nan,np.nan], equal_nan=True)
        np.testing.assert_allclose(feature('VV_MINUS_VH_DB',bands), [6])
        np.testing.assert_allclose(feature('VV',{'VV':np.array([.1,0])},'linear'), [-10,np.nan], equal_nan=True)

    def test_mean_median_std_missing(self):
        stack = np.array([[1,np.nan],[2,np.nan],[9,np.nan]], dtype='float32')
        np.testing.assert_allclose(aggregate(stack,'mean'), [4,np.nan], equal_nan=True)
        np.testing.assert_allclose(aggregate(stack,'median'), [2,np.nan], equal_nan=True)
        self.assertAlmostEqual(float(aggregate(stack,'std')[0]), float(np.std([1,2,9])), places=5)

    def test_fusion_disagreement_and_missingness(self):
        optical = np.array([1,0,1,0,np.nan], dtype='float32')
        sar = np.array([1,0,0,1,1], dtype='float32')
        result, agree, disagree = fuse(optical,sar,'optical_and_sar')
        np.testing.assert_allclose(result,[1,0,0,0,np.nan],equal_nan=True)
        np.testing.assert_allclose(disagree,[0,0,1,1,np.nan],equal_nan=True)
        np.testing.assert_allclose(agree,[1,1,0,0,np.nan],equal_nan=True)
        np.testing.assert_allclose(fuse(optical,sar,'optical_or_sar')[0],[1,0,1,1,np.nan],equal_nan=True)
        np.testing.assert_allclose(fuse(optical,sar,'weighted_confidence')[0],[1,0,1,0,np.nan],equal_nan=True)
        with self.assertRaises(ValueError):
            fuse(optical,sar,'weighted_confidence',.8,.8)

    def test_component_semantics(self):
        a = np.zeros((5,5),dtype='float32'); a[0,0]=1; a[2,2]=1; a[3,3]=1; a[4,0]=np.nan
        result=clean(a,2)
        self.assertEqual(result[0,0],0); self.assertEqual(result[2,2],1); self.assertTrue(np.isnan(result[4,0]))

    def test_equal_area_policy_and_tile_edges(self):
        grid = Grid('EPSG:6933',Affine(20,0,0,0,-20,0),9,7)
        self.assertAlmostEqual(grid.pixel_ha,.04)
        self.assertEqual(sum(w.width*w.height for w in tiles(grid,4)),63)
        with self.assertRaises(ValueError):
            Grid('EPSG:4326',Affine(.1,0,0,0,-.1,0),2,2).pixel_ha
        with self.assertRaises(ValueError):
            Grid('EPSG:32635',Affine(20,0,0,0,-20,0),2,2).pixel_ha


class TemporalTests(unittest.TestCase):
    def config(self, mode='moving-window'):
        return {'temporal':{'mode':mode,'alignment':'relative-day','target':{'start':'2026-06-01','end':'2026-08-31'},'reference_periods':[{'start':'2025-06-01','end':'2025-08-31'},{'start':'2024-06-01','end':'2024-08-31'}],'window_days':30,'step_days':10,'aggregation':'median'}}

    def test_moving_complete_half_open(self):
        w=windows(self.config())
        self.assertEqual(len(w),7)
        self.assertEqual(w[0]['target'],['2026-06-01','2026-07-01'])
        self.assertEqual(w[-1]['target'],['2026-07-31','2026-08-30'])
        self.assertEqual(w[2]['references'][0],['2025-06-21','2025-07-21'])

    def test_matched_season_alignment_and_southern_season(self):
        c=self.config('matched-season'); c['temporal']['alignment']='calendar-date'
        self.assertEqual(len(windows(c)),1)
        c['temporal']['reference_periods'][0]['start']='2025-05-01'
        with self.assertRaises(ValueError): windows(c)
        c=self.config('matched-season-moving-window'); c['temporal']['alignment']='calendar-date'
        self.assertEqual(len(windows(c)),7)
        c={'temporal':{'mode':'matched-season','alignment':'calendar-date','target':{'start':'2025-12-01','end':'2026-02-28'},'reference_periods':[{'start':'2024-12-01','end':'2025-02-28'}]}}
        self.assertEqual(windows(c)[0]['references'][0],['2024-12-01','2025-03-01'])

    def test_monthly_leap_end(self):
        c={'temporal':{'mode':'monthly','target':{'start':'2024-02-01','end':'2024-02-29'},'reference_periods':[{'start':'2023-02-01','end':'2023-02-28'}]}}
        self.assertEqual(windows(c)[0]['target'][1],'2024-03-01')

    def test_invalid_window_parameters_and_alignment(self):
        c=self.config(); c['temporal']['step_days']=0
        with self.assertRaises(ValueError): windows(c)
        c=self.config(); c['temporal']['alignment']='implicit'
        with self.assertRaises(ValueError): windows(c)
        c=self.config(); c['temporal']['reference_periods'][0]['end']='2025-08-30'
        with self.assertRaises(ValueError): windows(c)


class LocalWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.paths=create_fixture(self.temp.name)

    def workflow(self, config=None, output=None):
        if config:
            self.paths[0].write_text(yaml.safe_dump(config))
        return Workflow(*self.paths, output_prefix=output)

    def test_provider_interface_spatial_temporal_filter_window_reads(self):
        w=self.workflow(); p=w.providers['optical']
        self.assertIsInstance(p, ObservationProvider)
        items=p.search(w.geometry,'2026-06-01','2026-06-15',{})
        self.assertEqual([i['id'] for i in items],['s2-2026-5'])
        self.assertEqual(p.search(w.geometry,'2026-06-01','2026-07-01',{'absent':'x'}),[])
        a=read_asset(p,items[0]['assets']['nir'],w.grid,Window(1,1,2,3))
        self.assertEqual(a.shape,(3,2))
        outside={'type':'Polygon','coordinates':[[[0,0],[1,0],[1,1],[0,1],[0,0]]]}
        self.assertEqual(p.search(outside,'2026-06-01','2026-07-01',{}),[])

    def test_stac_interface_query_inventory_and_equivalence(self):
        w=self.workflow(); local=w.providers['optical']; items=local.search(w.geometry,'2026-06-01','2026-07-01',{})
        raw=[{'id':i['id'],'type':'Feature','geometry':i['geometry'],'properties':{**i['properties'],'datetime':i['datetime']},'assets':i['assets']} for i in items]
        mocked=[Mock(to_dict=Mock(return_value=i)) for i in raw]
        client=Mock(); client.search.return_value.items.return_value=iter(mocked)
        cfg={'endpoint':'https://example.invalid/stac','collection':'synthetic','asset_map':{k:k for k in items[0]['assets']}}
        stac=STACProvider(cfg,client=client)
        found=stac.search(w.geometry,'2026-06-01','2026-07-01',{})
        self.assertEqual([i['id'] for i in found],[i['id'] for i in items])
        self.assertEqual(client.search.call_args.kwargs['datetime'],'2026-06-01T00:00:00Z/2026-07-01T00:00:00Z')
        win=Window(0,0,3,3)
        np.testing.assert_allclose(read_asset(stac,found[0]['assets']['nir'],w.grid,win),read_asset(local,items[0]['assets']['nir'],w.grid,win))
        record=stac.record_query(w.geometry,'2026-06-01','2026-07-01',{},found)
        self.assertEqual(len(record['query_geometry_hash']),64)
        cfg['asset_calibration']={'nir':{'scale':2,'offset':.1}}
        client.search.return_value.items.return_value=iter(mocked)
        calibrated=STACProvider(cfg,client=client).search(w.geometry,'2026-06-01','2026-07-01',{})
        np.testing.assert_allclose(read_asset(stac,calibrated[0]['assets']['nir'],w.grid,win),
                                   read_asset(local,items[0]['assets']['nir'],w.grid,win)*2+.1)

    def test_end_to_end_area_gating_disagreement_manifest(self):
        w=self.workflow(); w.run()
        summary=load(w.out/'loss_area_summary.json')
        self.assertAlmostEqual(summary['disturbed_ha_total'],.16,places=5)
        def count(name):
            with rasterio.open(w.path('w0000',name)) as src:
                return np.count_nonzero(src.read(1,masked=True).filled(-9999)==1)
        self.assertEqual(count('optical_candidate'),14)
        self.assertEqual(count('sar_candidate'),16)
        self.assertEqual(count('disagreement'),22)
        manifest=load(w.out/'run_manifest.json')
        self.assertEqual(manifest['features_used']['optical'],['NDVI','NDMI','NBR'])
        self.assertEqual(manifest['area_method']['crs'],'EPSG:6933')
        self.assertTrue(all(len(o['sha256'])==64 for o in manifest['outputs']))
        self.assertTrue((w.out/'w0000/qa.png').exists())
        first=(w.out/'run_manifest.json').read_bytes()
        w.report()
        self.assertEqual(first,(w.out/'run_manifest.json').read_bytes())
        # Same selected inventory and algorithms produce byte-identical rasters across tile sizes.
        config=load(self.paths[0]); config['execution']['tile_size']=16
        wide=self.workflow(config, str(Path(self.temp.name)/'wide')); wide.run()
        for name in ('NDVI_current','NDVI_change','sar_candidate','disturbance','disagreement'):
            with rasterio.open(w.path('w0000',name)) as a,rasterio.open(wide.path('w0000',name)) as b:
                np.testing.assert_allclose(a.read(1),b.read(1))

    def test_component_halo_across_tiles(self):
        c=load(self.paths[0]); c['threshold']['min_component_pixels']=4
        small=self.workflow(c); small.run()
        c['execution']['tile_size']=16
        wide=self.workflow(c,str(Path(self.temp.name)/'wide')); wide.run()
        with rasterio.open(small.path('w0000','disturbance')) as a, rasterio.open(wide.path('w0000','disturbance')) as b:
            np.testing.assert_allclose(a.read(1),b.read(1))
        self.assertAlmostEqual(load(small.out/'loss_area_summary.json')['disturbed_ha_total'],.16)

    def test_sar_geometry_rejection_and_config_snapshot_guard(self):
        w=self.workflow(); inv=load(Path(self.temp.name)/'sar.json'); inv['items'][-1]['properties']['sat:relative_orbit']=43
        write_json(Path(self.temp.name)/'sar.json',inv)
        w=self.workflow()
        with self.assertRaisesRegex(ValueError,'acquisition geometry'): w.discovery()
        c=load(self.paths[0]); c['threshold']['value']=-.5
        changed=self.workflow(c)
        with self.assertRaisesRegex(ValueError,'different configuration'): changed.discovery()

    def test_missing_optical_not_zero_and_sar_only(self):
        inv=load(Path(self.temp.name)/'optical.json'); inv['items']=[i for i in inv['items'] if not i['datetime'].startswith('2026')]
        write_json(Path(self.temp.name)/'optical.json',inv)
        w=self.workflow(); w.run()
        with rasterio.open(w.path('w0000','fused_candidate')) as src:
            self.assertTrue(src.read(1,masked=True).mask.all())
        c=load(self.paths[0]); c['fusion']['mode']='sar_only'
        w=self.workflow(c,str(Path(self.temp.name)/'sar-only')); w.run()
        summary=load(w.out/'loss_area_summary.json')
        self.assertAlmostEqual(summary['disturbed_ha_total'],.64,places=5)
        self.assertTrue(summary['evidence_mode']['degraded_sar_only'])
        self.assertTrue(any(l.startswith('Degraded SAR-only') for l in load(w.out/'run_manifest.json')['limitations']))

    def test_schema_and_lab_contracts(self):
        c=load(self.paths[0]); schema=json.loads((ROOT/'specs/workflow.schema.json').read_text())
        Draft202012Validator(schema).validate(c)
        lab=ROOT.parent/'forest-cover-lab'
        if not lab.exists(): self.skipTest('Forest Cover Lab not local')
        spec=importlib.util.spec_from_file_location('lab_graph', lab/'graph/build.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        graph=json.loads((lab/'graph/generated/knowledge.json').read_text())
        mod.validate_descriptor(load(ROOT/'workflow.yaml'),graph,root=lab)
        w=self.workflow(); w.run()
        mod.validate_provenance(load(w.out/'run_manifest.json'),graph,root=lab)

    def test_application_must_be_lab_concept_id(self):
        c=load(self.paths[0]); c['application']='seasonal-forest-change'
        with self.assertRaises(ValidationError): normalize(c)

    def lab(self):
        lab=ROOT.parent/'forest-cover-lab'
        if not lab.exists(): self.skipTest('Forest Cover Lab not local')
        spec=importlib.util.spec_from_file_location('lab_graph', lab/'graph/build.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        return mod, json.loads((lab/'graph/generated/knowledge.json').read_text()), lab

    def test_seasonal_s1_s2_semantic_example_end_to_end(self):
        # docs/semantic_example.md: JJA 2026 vs 2024/2025, 30-day windows, 10-day step, S1+S2, local Python.
        c=load(self.paths[0])
        c['temporal'].update(mode='matched-season-moving-window', window_days=30, step_days=10,
            target={'start':'2026-06-01','end':'2026-08-31'},
            reference_periods=[{'start':'2024-06-01','end':'2024-08-31'},{'start':'2025-06-01','end':'2025-08-31'}])
        w=self.workflow(c,str(Path(self.temp.name)/'seasonal')); w.run()
        summary=load(w.out/'loss_area_summary.json')
        self.assertEqual([x['target'][0] for x in summary['windows']][::3],['2026-06-01','2026-07-01','2026-07-31'])
        self.assertNotIn('disturbed_ha_total',summary)
        self.assertEqual(summary['evidence_mode']['fusion'],'optical_and_sar')
        # Fixture observations exist only in June; later windows stay nodata rather than becoming absence.
        late=[q for q in load(w.out/'observation_inventory.json')['queries'] if q['window_id']=='w0006']
        self.assertTrue(late and all(q['items']==[] for q in late))
        with rasterio.open(w.path('w0006','fused_candidate')) as src:
            self.assertTrue(src.read(1,masked=True).mask.all())
        sp=load(w.out/'run_manifest.json')['semantic_provenance']
        methods=[m['id'] for m in sp['methods']]
        self.assertEqual(methods,['method:matched-season-interannual-comparison','method:moving-window-comparison',
                                  'method:ndvi-anomaly','method:s1-backscatter-confirmation'])
        self.assertEqual([t['id'] for t in sp['tools']],['tool:pyproj','tool:rasterio','tool:shapely'])
        self.assertIn('application:seasonal-forest-change-monitoring',sp['concept_ids'])
        self.assertEqual(sp['workflow']['id'],'workflow:sentinel-monthly-forest-cover')
        mod,graph,lab=self.lab()
        mod.validate_provenance(load(w.out/'run_manifest.json'),graph,root=lab)
        trace=explain(w.config,load(ROOT/'workflow.yaml'),graph)
        self.assertEqual([m['id'] for m in trace['methods_selected_by_configuration']],methods)
        self.assertFalse(trace['gee_required'])
        self.assertEqual(trace['configuration']['window_count'],7)

    def test_semantic_trace_cli_and_unresolved_application(self):
        mod,graph,lab=self.lab()
        out=subprocess.run([sys.executable,str(ROOT/'scripts/explain_semantic_path.py'),'--config',str(ROOT/'configs/workflow.example.yaml'),'--lab',str(lab)],
                           check=True,capture_output=True,text=True).stdout
        trace=json.loads(out)
        self.assertEqual(trace['configured_datasets'],{'optical':'DS-0002','sar':'DS-0003'})
        self.assertEqual(trace['access']['DS-0002']['selected_route']['id'],'access:live-catalogue')
        c=load(self.paths[0]); c['application']='application:missing'
        with self.assertRaisesRegex(ValueError,'Unresolved application'):
            explain(normalize(c),load(ROOT/'workflow.yaml'),graph)

    def test_legacy_manifest_explicit_migration_error(self):
        with self.assertRaisesRegex(ValueError,'explicit providers'):
            normalize(load(ROOT/'configs/legacy_gee_manifest.example.json'))

    def test_legacy_monthly_migration_with_explicit_local_inputs(self):
        old=load(ROOT/'configs/legacy_gee_manifest.example.json'); new=load(self.paths[0])
        old['current_month']=6
        old['reference_years']=[2024,2025]
        for key in ('observations','providers','execution','forest_mask','output'):
            old[key]=new[key]
        old['threshold'].pop('max_cloud_fraction')
        old['threshold']['min_component_pixels']=1
        migrated=normalize(old)
        self.assertEqual(migrated['temporal']['mode'],'monthly')
        self.assertEqual(migrated['temporal']['reference_statistic'],'pooled-observations')
        self.assertEqual(migrated['fusion']['mode'],'optical_and_sar')
        self.assertEqual(migrated['observations']['optical']['features'],['NDVI'])
        self.assertEqual(migrated['observations']['sar']['thresholds']['VV'],-1.5)
        w=self.workflow(migrated); w.run()
        self.assertAlmostEqual(load(w.out/'loss_area_summary.json')['disturbed_ha_total'],.16,places=5)

    def test_moving_modes_end_to_end_separate_window_summaries(self):
        for mode, alignment in [('moving-window','relative-day'),('matched-season-moving-window','calendar-date')]:
            c=load(self.paths[0]); c['temporal'].update(mode=mode, alignment=alignment,window_days=15,step_days=10)
            w=self.workflow(c,str(Path(self.temp.name)/mode)); w.run()
            summary=load(w.out/'loss_area_summary.json')
            self.assertEqual(len(summary['windows']),2)
            self.assertNotIn('disturbed_ha_total',summary)
            self.assertEqual(len(load(w.out/'run_manifest.json')['temporal_windows']),2)

    def test_inputs_changed_after_discovery_rejected(self):
        w=self.workflow(); w.discovery()
        with rasterio.open(Path(self.temp.name)/'forest.tif','r+') as src:
            src.write(np.zeros((10,10),dtype='float32'),1)
        with self.assertRaisesRegex(ValueError,'baseline changed'): w.composites()

    def test_production_no_earth_engine_import(self):
        code="import builtins\noriginal=builtins.__import__\ndef guarded(name,*a,**k):\n if name.split('.')[0] in ('ee','geemap','google'): raise AssertionError(name)\n return original(name,*a,**k)\nbuiltins.__import__=guarded\nfrom forest_change.pipeline import Workflow\n"
        subprocess.run([sys.executable,'-c',code],cwd=ROOT,check=True,capture_output=True)
        for path in [*(ROOT/'scripts').glob('*.py'), *(ROOT/'forest_change').glob('*.py')]:
            self.assertNotIn('import ee',path.read_text())
            self.assertNotIn('import geemap',path.read_text())
        requirements=(ROOT/'requirements.txt').read_text().lower()
        for package in ('earthengine','geemap','google-cloud'):
            self.assertNotIn(package,requirements)


if __name__=='__main__': unittest.main()
