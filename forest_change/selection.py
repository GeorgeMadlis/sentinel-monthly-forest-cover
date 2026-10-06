"""Deterministic AOI-quality ranking of actual catalogue observations."""
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import rasterio
from rasterio.windows import Window
from .raster import grid_for, inside, read_asset
from .temporal import period


def rank_key(record):
    m = record['metrics']
    return (-m['aoi_valid_pixel_fraction'], m['aoi_cloud_shadow_fraction'],
            m['scene_cloud_percentage'] if m['scene_cloud_percentage'] is not None else 101,
            m['central_date_distance_seconds'], record['item']['id'])


def rank_observations(items, provider, geometry, requested_period, resolution=200, resolver=None, progress=None):
    grid, projected = grid_for(geometry, {'crs':'EPSG:6933', 'resolution':resolution})
    window = Window(0, 0, grid.width, grid.height)
    gate = inside(projected, grid, window)
    start, end = period(requested_period)
    centre = datetime.combine(start, datetime.min.time(), timezone.utc) + (end-start)/2
    records = []
    def assess(item):
        asset = item['assets']['scl']
        if resolver:
            asset, _ = resolver.resolve(item, 'scl', asset)
        try:
            scl = read_asset(provider, asset, grid, window, categorical=True)
        except (OSError, rasterio.errors.RasterioError):
            if not resolver:
                raise
            asset, _ = resolver.resolve(item, 'scl', item['assets']['scl'], remote_failed=True)
            scl = read_asset(provider, asset, grid, window, categorical=True)
        covered = gate & np.isfinite(scl) & (scl != 0) & (scl != 1)
        cloud = covered & np.isin(scl, [3,8,9,10])
        quality = gate & np.isin(scl, [4,5,6,7])
        stamp = datetime.fromisoformat(item['datetime'].replace('Z','+00:00'))
        metrics = {'aoi_valid_pixel_fraction':float(covered.sum()/gate.sum()),
                   'aoi_cloud_shadow_fraction':float(cloud.sum()/max(1,covered.sum())),
                   'aoi_clear_pixel_fraction':float(quality.sum()/gate.sum()),
                   'scene_cloud_percentage':item['properties'].get('eo:cloud_cover'),
                   'central_date_distance_seconds':abs((stamp-centre).total_seconds()),
                   'assessment_resolution_m':resolution}
        return {'item':item, 'metrics':metrics}
    with ThreadPoolExecutor(max_workers=8) as executor:
        for index, record in enumerate(executor.map(assess, items)):
            records.append(record)
            if progress:
                progress(index+1, len(items), record['item']['id'])
    ranked = sorted(records, key=rank_key)
    usable = [r for r in ranked if r['metrics']['aoi_clear_pixel_fraction'] > 0]
    if not usable:
        raise ValueError('No usable observation with clear AOI pixels')
    return usable[0], ranked
