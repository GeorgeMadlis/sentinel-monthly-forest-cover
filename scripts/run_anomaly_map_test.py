"""Select real Sentinel-2 observations and create a portable Leaflet evidence map."""
import argparse
import os
os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
os.environ.setdefault("GDAL_HTTP_TIMEOUT", "60")
os.environ.setdefault("GDAL_HTTP_MAX_RETRY", "2")
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from forest_change.anomaly_map import run

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',default='configs/anomaly-map.example.yaml')
    parser.add_argument('--aoi',default='configs/aoi.example.geojson')
    parser.add_argument('--output-prefix')
    parser.add_argument('--replay-from',help='Reprocess verified source AOI windows from a previous run into a new output directory')
    parser.add_argument('--asset-access',choices=['auto','remote','cache'],default='auto')
    args=parser.parse_args()
    if args.replay_from:
        from forest_change.replay import replay
        replay(args.manifest,args.aoi,args.replay_from,args.output_prefix)
    else:
        run(args.manifest,args.aoi,args.output_prefix,args.asset_access)
