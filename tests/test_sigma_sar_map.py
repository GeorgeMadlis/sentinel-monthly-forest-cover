"""Decision boundary, missing evidence and same-track selection checks."""
import unittest
import tempfile
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import rasterio
from affine import Affine
from shapely.geometry import box, mapping
from forest_change.evidence import write_json, load
from forest_change.raster import Grid
from forest_change.sigma_sar_map import sigma_candidate, radar_candidate, choose_track, radar_reference_medians


class SigmaRadarTests(unittest.TestCase):
    def test_radar_reference_uses_median_rather_than_pooled_mean(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            grid=Grid('EPSG:6933',Affine(20,0,0,0,-20,20),1,1)
            for feature in ['VV','VH']:
                with rasterio.open(root/(feature+'_reference.tif'),'w',**grid.profile) as dst:
                    dst.write(np.array([[99]],dtype='float32'),1)
            write_json(root/'composites_tiles.json',{})
            inventory={'queries':[{'sensor':'sar','role':'reference','window_id':'w',
                                   'items':[{'id':str(i)} for i in range(3)]}]}
            def stack(sensor,items,obs,tile):
                self.assertEqual(sensor,'sar')
                self.assertEqual(len(items),3)
                return {'VV':np.array([1,2,9],dtype='float32').reshape(3,1,1),
                        'VH':np.array([2,3,10],dtype='float32').reshape(3,1,1)}
            workflow=SimpleNamespace(inventory=lambda:inventory,config={'observations':{'sar':{}}},
                                     windows=[{'id':'w'}],grid=grid,size=512,out=root,
                                     projected=mapping(box(0,0,20,20)),feature_stack=stack,
                                     path=lambda wid,name:root/(name+'.tif'))
            radar_reference_medians(workflow)
            for feature,expected in [('VV',2),('VH',3)]:
                with rasterio.open(root/(feature+'_reference.tif')) as src:
                    self.assertEqual(src.read(1)[0,0],expected)
            self.assertIn('median',load(root/'composites_tiles.json')['sar_reference_statistic'])

    def test_strict_sigma_boundary_and_missing_reference(self):
        current = np.array([.25, .24, .24, .24, np.nan])
        result = sigma_candidate(current, np.full(5,.5), np.array([.125,.125,0,.125,.125]),
                                 np.array([2,2,2,1,2]), 2)
        np.testing.assert_allclose(result, [0,1,np.nan,np.nan,np.nan], equal_nan=True)

    def test_both_radar_decreases_required_and_missing_is_not_negative(self):
        result = radar_candidate(np.array([-1.5,-1.6,-2,-2,np.nan]),
                                 np.array([-2,-1,-1.1,np.nan,-2]))
        np.testing.assert_allclose(result, [0,0,1,np.nan,np.nan], equal_nan=True)

    def test_track_selection_excludes_partial_coverage_and_other_tracks(self):
        aoi = {'type':'Polygon','coordinates':[[[0,0],[1,0],[1,1],[0,1],[0,0]]]}
        def item(day, track, geometry=aoi):
            return {'id':f'{day}-{track}', 'geometry':geometry,
                    'properties':{'datetime':day+'T00:00:00Z','sat:orbit_state':'ascending','sat:relative_orbit':track}}
        groups = {'reference':[item('2025-06-01',42),item('2025-06-13',42),item('2025-06-25',42)],
                  'target':[item('2026-06-01',42),item('2026-06-13',42),item('2026-06-25',42),item('2026-06-01',99)]}
        partial = {'type':'Polygon','coordinates':[[[0,0],[.5,0],[.5,1],[0,1],[0,0]]]}
        groups['reference'].extend([item('2025-06-01',99,partial),item('2025-06-13',99,partial)])
        groups['target'].append(item('2026-06-13',99,partial))
        track, periods = choose_track(groups,aoi,2)
        self.assertEqual(track,('ascending',42))
        self.assertEqual([v['properties']['datetime'][:10] for v in periods['reference']],['2025-06-01','2025-06-25'])
        groups['reference'] = groups['reference'][:1]
        with self.assertRaises(ValueError):
            choose_track(groups,aoi,2)
