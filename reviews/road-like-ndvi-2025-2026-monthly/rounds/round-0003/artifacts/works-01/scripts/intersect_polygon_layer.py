"""Area overlap of ROI polygons (EPSG:4326 input) with a polygon layer in EPSG:3301. Usage: python -I intersect_polygon_layer.py ROI_GEOJSON LAYER_JSON"""
import json, sys
from shapely.geometry import shape
from shapely.ops import transform, unary_union
from pyproj import Transformer
tr = Transformer.from_crs(4326, 3301, always_xy=True).transform
rois = {f['properties']['id']: transform(tr, shape(f['geometry'])) for f in json.load(open(sys.argv[1]))['features']}
lay = json.load(open(sys.argv[2]))['features']
U = unary_union([shape(f['geometry']) for f in lay])
print('layer features', len(lay), 'area_ha', round(U.area/1e4,1))
for rid, p in rois.items():
    i = p.intersection(U)
    # along-axis coverage: split ROI by 250 m slices along its main direction is approximated by sampling points on the ROI boundary-derived axis
    print(rid, 'roi_area_m2', round(p.area), 'inside_m2', round(i.area), 'pct', round(100*i.area/p.area,1), 'min_dist_m', round(p.distance(U),1))
