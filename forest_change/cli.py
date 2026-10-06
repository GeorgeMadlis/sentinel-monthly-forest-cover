import argparse
from .pipeline import Workflow


def main(stage='all'):
    p = argparse.ArgumentParser(description='GEE-independent Sentinel forest disturbance evidence')
    p.add_argument('--manifest', required=True, help='Workflow JSON/YAML (schema 2.0 or explicit legacy migration)')
    p.add_argument('--forest-def', required=True)
    p.add_argument('--aoi-geojson', required=True)
    p.add_argument('--output-prefix', default=None)
    p.add_argument('--service-account-key', default='', help='Deprecated; rejected by local backend')
    p.add_argument('--ee-project', default='', help='Deprecated; rejected by local backend')
    args = p.parse_args()
    if args.service_account_key or args.ee_project:
        p.error('Earth Engine options apply only to examples/gee/')
    Workflow(args.manifest, args.forest_def, args.aoi_geojson, args.output_prefix).run(stage)
