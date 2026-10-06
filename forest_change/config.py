from copy import deepcopy
from pathlib import Path
import math
import json
from jsonschema import Draft202012Validator, FormatChecker

from .algorithms import OPTICAL
from .evidence import load
from .temporal import monthly, windows


def normalize(raw):
    c = deepcopy(raw)
    if 'schema_version' not in c:
        if c.get('reference_strategy') != 'same-month-last-3-years':
            raise ValueError('Unsupported legacy reference strategy; migrate explicitly')
        if 'providers' not in c or 'execution' not in c or 'forest_mask' not in c:
            raise ValueError('Legacy GEE manifest requires explicit providers, execution grid and forest_mask. See docs/migration.md or examples/gee/run_pipeline.py.')
        c['schema_version'] = '2.0'
        c['temporal'] = {'mode': 'monthly', 'target': monthly(c['current_year'], c['current_month']),
                         'reference_periods': [monthly(y, c['current_month']) for y in c['reference_years']],
                         'aggregation': 'median', 'reference_statistic': 'pooled-observations'}
        supplied = c.get('observations', {})
        c['observations'] = {'optical': {**supplied.get('optical', {}), 'dataset': 'DS-0002', 'features': ['NDVI']}}
        s1 = c.get('s1_confirmation', {})
        if s1.get('enabled'):
            c['observations']['sar'] = {**supplied.get('sar', {}), 'dataset': 'DS-0003', 'features': ['VV', 'VH'],
                                      'units': 'db', 'aggregation': 'median',
                                      'thresholds': {'VV': s1.get('vv_drop_db', -1.5), 'VH': s1.get('vh_drop_db', -1)}}
        c['fusion'] = {'mode': 'optical_and_sar' if s1.get('enabled') else 'optical_only'}
        if c.get('tiling', {}).get('tile_size_degrees'):
            c.setdefault('migration_notes', []).append('Legacy degree tiles replaced by explicit execution.tile_size pixels; summaries use new tile IDs.')
    if c['schema_version'] != '2.0':
        raise ValueError('Unsupported workflow schema version')
    if 'max_cloud_fraction' in c.get('threshold', {}):
        raise ValueError('Legacy max_cloud_fraction requires explicit migration to pixel quality; see docs/migration.md')
    for p in [c['temporal']['target'], *c['temporal']['reference_periods']]:
        p['start'], p['end'] = str(p['start']), str(p['end'])
    schema = json.loads((Path(__file__).resolve().parents[1] / 'specs/workflow.schema.json').read_text())
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(c)
    ex = c['execution']
    if ex.get('backend') != 'local-python':
        raise ValueError('Only local-python execution is implemented')
    for key in ('tile_size', 'max_observations_per_window'):
        ex.setdefault(key, 256 if key == 'tile_size' else 256)
        if not isinstance(ex[key], int) or ex[key] <= 0:
            raise ValueError(f'{key} must be a positive integer')
    if not math.isfinite(float(ex['resolution'])) or ex['resolution'] <= 0:
        raise ValueError('Resolution must be finite and positive')
    if c['temporal'].get('aggregation') not in ('mean', 'median'):
        raise ValueError('Temporal aggregation must be mean or median')
    if c['temporal'].get('reference_statistic', 'period-composites') not in ('period-composites', 'pooled-observations'):
        raise ValueError('Unsupported reference_statistic')
    obs = c['observations']
    for sensor, o in obs.items():
        if sensor not in ('optical', 'sar') or not o['features']:
            raise ValueError('Observations must contain optical/sar with nonempty features')
        allowed = OPTICAL if sensor == 'optical' else ('VV', 'VH', 'VV_MINUS_VH_DB')
        if any(f not in allowed for f in o['features']):
            raise ValueError(f'Unsupported {sensor} feature')
        if o['dataset'] != ('DS-0002' if sensor == 'optical' else 'DS-0003'):
            raise ValueError('Sentinel sensor dataset IDs must be DS-0002/DS-0003')
        if sensor not in c['providers']:
            raise ValueError(f'Missing {sensor} provider')
        p = c['providers'][sensor]
        if not o.get('version'):
            raise ValueError(f'{sensor} dataset version must be explicit')
        if sensor == 'optical' and not o.get('quality'):
            raise ValueError('Optical pixel quality configuration required (SCL or pre-masked)')
        if sensor == 'sar':
            if o.get('units') not in ('db', 'linear') or o.get('aggregation', c['temporal']['aggregation']) not in ('mean', 'median'):
                raise ValueError('Explicit SAR units and mean/median aggregation required')
            for key in ('orbit_direction', 'relative_orbit', 'instrument_mode', 'terrain_flattening', 'speckle_treatment'):
                if key not in o.get('preprocessing', {}):
                    raise ValueError(f'SAR preprocessing must declare {key}')
            if not o.get('thresholds') or any(f not in o['thresholds'] for f in o['features']):
                raise ValueError('Every SAR decision feature requires a current-minus-reference threshold')
    mode = c.get('fusion', {}).get('mode', 'optical_only')
    if mode not in ('optical_only', 'sar_only', 'optical_and_sar', 'optical_or_sar', 'weighted_confidence'):
        raise ValueError('Unknown fusion mode')
    required = {'optical'} if mode == 'optical_only' else {'sar'} if mode == 'sar_only' else {'optical', 'sar'}
    if not required <= obs.keys():
        raise ValueError('Fusion mode requires unavailable sensor configuration')
    thr = c.setdefault('threshold', {'mode': 'fixed', 'value': -.2})
    if thr.get('mode') not in ('fixed', 'sigma'):
        raise ValueError('Threshold mode must be fixed or sigma')
    if thr.get('mode') == 'sigma' and thr.get('k', 0) <= 0:
        raise ValueError('Sigma threshold requires positive k')
    if thr.get('mode') == 'fixed' and not math.isfinite(float(thr['value'])):
        raise ValueError('Fixed threshold must be finite')
    if thr.get('min_component_pixels', 1) < 1:
        raise ValueError('min_component_pixels must be positive')
    if not 0 <= thr.get('min_valid_pixel_ratio', 0) <= 1:
        raise ValueError('min_valid_pixel_ratio must lie in [0,1]')
    if c.get('persistence', {}).get('periods', 1) != 1:
        raise ValueError('Persistence-confirmed labels are not implemented; periods must be 1')
    fm = c['forest_mask']
    if fm is not None:
        for k in ('path', 'dataset', 'version', 'reference_year', 'threshold', 'transformation'):
            if k not in fm:
                raise ValueError(f'Forest mask must declare {k}')
        if fm['transformation'] != 'threshold-gte':
            raise ValueError('Only explicit threshold-gte forest mask transformation supported; supply transformed baseline')
    windows(c)
    if len(c['temporal']['reference_periods']) > c['execution']['max_observations_per_window']:
        raise ValueError('Reference-period count exceeds configured tile stack budget')
    return c


def read_config(path):
    c = load(path)
    # File references are relative to config/inventory files, never implicit working directory.
    root = Path(path).resolve().parent
    for p in c.get('providers', {}).values():
        if p.get('type') == 'local':
            p['inventory'] = str((root / p['inventory']).resolve())
    if c.get('forest_mask'):
        c['forest_mask']['path'] = str((root / c['forest_mask']['path']).resolve())
    return normalize(c)
