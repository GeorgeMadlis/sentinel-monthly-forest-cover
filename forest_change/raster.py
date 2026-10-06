from dataclasses import dataclass
import math

import numpy as np
import rasterio
from affine import Affine
from pyproj import CRS
from rasterio.enums import Resampling
from rasterio.features import geometry_mask
from rasterio.vrt import WarpedVRT
from rasterio.warp import transform_geom
from rasterio.windows import Window
from shapely.geometry import shape, mapping
from shapely.ops import unary_union


@dataclass
class Grid:
    crs: str
    transform: Affine
    width: int
    height: int

    @property
    def profile(self):
        return dict(driver='GTiff', width=self.width, height=self.height, count=1,
                    crs=self.crs, transform=self.transform, dtype='float32', nodata=-9999,
                    tiled=True, blockxsize=256, blockysize=256, compress='deflate',
                    BIGTIFF='IF_SAFER')  # country grids can exceed 4 GiB per layer

    @property
    def pixel_ha(self):
        crs = CRS.from_user_input(self.crs)
        method = crs.coordinate_operation.method_name.lower() if crs.coordinate_operation else ''
        if not crs.is_projected or ('equal area' not in method and 'equal-area' not in method):
            raise ValueError('Area integration requires a projected equal-area CRS')
        factors = [a.unit_conversion_factor for a in crs.axis_info[:2]]
        return abs(self.transform.a*self.transform.e-self.transform.b*self.transform.d)*factors[0]*factors[1]/10000


def aoi_geometry(raw):
    if raw['type'] == 'FeatureCollection':
        geoms = [shape(f['geometry']) for f in raw['features']]
        if not geoms:
            raise ValueError('Empty AOI')
        g = unary_union(geoms)
    else:
        g = shape(raw['geometry'] if raw['type'] == 'Feature' else raw)
    if g.is_empty or not g.is_valid or g.geom_type not in ('Polygon', 'MultiPolygon'):
        raise ValueError('AOI must be valid nonempty Polygon/MultiPolygon in EPSG:4326')
    if g.bounds[2]-g.bounds[0] > 180:
        raise ValueError('Split antimeridian AOIs before processing')
    return mapping(g)


def grid_for(geometry, execution):
    crs, res = execution['crs'], float(execution['resolution'])
    projected = transform_geom('EPSG:4326', crs, geometry)
    left, bottom, right, top = shape(projected).bounds
    left, bottom = math.floor(left/res)*res, math.floor(bottom/res)*res
    right, top = math.ceil(right/res)*res, math.ceil(top/res)*res
    grid = Grid(crs, Affine(res, 0, left, 0, -res, top), round((right-left)/res), round((top-bottom)/res))
    grid.pixel_ha  # validate before allocating artifacts
    return grid, projected


def tiles(grid, size):
    for row in range(0, grid.height, size):
        for col in range(0, grid.width, size):
            yield Window(col, row, min(size, grid.width-col), min(size, grid.height-row))


def expand(window, halo, grid):
    left, top = max(0, window.col_off-halo), max(0, window.row_off-halo)
    right, bottom = min(grid.width, window.col_off+window.width+halo), min(grid.height, window.row_off+window.height+halo)
    return Window(left, top, right-left, bottom-top)


def inside(geometry, grid, window):
    return geometry_mask([geometry], out_shape=(int(window.height), int(window.width)),
                         transform=rasterio.windows.transform(window, grid.transform), invert=True)


def read_asset(provider, asset, grid, window, categorical=False):
    with provider.open_asset(asset) as src:
        with WarpedVRT(src, crs=grid.crs, transform=grid.transform, width=grid.width,
                       height=grid.height, dtype='float32', nodata=np.nan,
                       resampling=Resampling.nearest if categorical else Resampling.bilinear) as vrt:
            values = vrt.read(int(asset.get('band', 1)), window=window, masked=True).filled(np.nan)
    # Explicit per-asset calibration wins; STAC raster extension is used otherwise.
    metadata = asset.get('raster:bands', [{}])[int(asset.get('band', 1))-1]
    scale = asset.get('scale', metadata.get('scale', 1))
    offset = asset.get('offset', metadata.get('offset', 0))
    calibrated = values if categorical else values*scale + offset
    return np.where(np.isfinite(calibrated), calibrated, np.nan).astype('float32')


def write_window(dst, values, window):
    dst.write(np.where(np.isfinite(values), values, -9999).astype('float32'), 1, window=window)
