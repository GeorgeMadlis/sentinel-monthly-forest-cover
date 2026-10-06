"""Map a run configuration onto pinned Forest Cover Lab concepts. Never defines new semantics."""
from .evidence import CLAIM_IDS, SENSOR_CONCEPTS
from .temporal import windows

TEMPORAL_METHODS = {'monthly': ['method:monthly-compositing'],
                    'moving-window': ['method:moving-window-comparison'],
                    'matched-season': ['method:matched-season-interannual-comparison'],
                    'matched-season-moving-window': ['method:matched-season-interannual-comparison',
                                                     'method:moving-window-comparison']}
PROVIDER_ACCESS = {'stac': 'access:live-catalogue'}
STAGE_ARTIFACTS = ['config_snapshot.json', 'observation_inventory.json', 'composites_metadata.json',
                   'composites_tiles.json', 'ndvi_anomaly_summary.json', 'loss_area_tiles.json',
                   'loss_area_tiles.csv', 'loss_area_summary.json', 'loss_area_summary.geojson',
                   'metrics.json', 'report.md', 'final_map.html', 'run_manifest.json']
DECISION_LAYERS = ['optical_candidate', 'sar_candidate', 'agreement', 'disagreement', 'fused_candidate', 'disturbance']
FEATURE_LAYERS = ['current', 'reference', 'reference_std', 'current_count', 'reference_count', 'change']


def selected_methods(config):
    obs = config['observations']
    methods = ['method:ndvi-anomaly'] if 'NDVI' in obs.get('optical', {}).get('features', []) else []
    if 'sar' in obs:
        methods.append('method:s1-backscatter-confirmation')
    return sorted(set(methods + TEMPORAL_METHODS[config['temporal']['mode']]))


def concept_ids(config, descriptor):
    sensors = config['observations']
    concepts = [i for i in descriptor['observation_ids'] if SENSOR_CONCEPTS.get(i) in (None, *sensors)]
    concepts += descriptor['validation_ids'] + CLAIM_IDS
    if config.get('application'):
        concepts.append(config['application'])
    return sorted(set(concepts))


def explain(config, descriptor, graph):
    """Resolve application -> methods -> observations -> datasets -> access/tools -> workflow."""
    nodes = {n['id']: n for n in graph['nodes']}
    edges = graph['relationships'] + graph['candidate_relationships']

    def out(source, relation):
        return [{'id': e['target'], 'status': e['status'], **({'scope': e['scope']} if 'scope' in e else {})}
                for e in edges if e['source'] == source and e['type'] == relation]

    def resolve(identifier, kind):
        if identifier not in nodes or nodes[identifier]['type'] != kind:
            raise ValueError(f'Unresolved {kind}: {identifier}')
        return identifier

    if graph['revision'] != descriptor['knowledge_snapshot']['graph_revision']:
        raise ValueError('Lab graph revision differs from workflow.yaml pin')
    application = resolve(config['application'], 'application')
    questions = out(application, 'ASKS')
    scientific = []
    pending = [m for q in questions for m in out(q['id'], 'ADDRESSED_BY')]
    while pending:
        m = pending.pop(0)
        if m['id'] not in [s['id'] for s in scientific]:
            scientific.append(m)
            pending += out(m['id'], 'USES_METHOD')
    workflow = resolve(descriptor['workflow_id'], 'workflow')
    implemented = {e['id']: e for e in out(workflow, 'IMPLEMENTS')}
    methods = selected_methods(config)
    for m in methods:
        resolve(m, 'method')
        if m not in implemented or m not in descriptor['implemented_method_ids']:
            raise ValueError(f'{m} is not implemented by {workflow}')
    observations = {m: out(m, 'REQUIRES_OBSERVATION') for m in methods}
    configured = {s: resolve(o['dataset'], 'dataset') for s, o in config['observations'].items()}
    observable = {o['id']: out(o['id'], 'CAN_BE_OBSERVED_BY') for obs in observations.values() for o in obs}
    for sensor, dataset in configured.items():
        if not any(d['id'] == dataset for ds in observable.values() for d in ds):
            raise ValueError(f'{dataset} ({sensor}) satisfies no required observation')
    providers = config['providers']
    access = {}
    for sensor, dataset in configured.items():
        kind = providers[sensor]['type']
        routes = out(dataset, 'ACCESSED_VIA')
        chosen = PROVIDER_ACCESS.get(kind)
        access[dataset] = {'lab_routes': routes, 'provider_type': kind,
                           'selected_route': next((r for r in routes if r['id'] == chosen), None)
                           or {'id': None, 'note': 'user-supplied local inventory; no Lab access record'}}
    tools = {t: [c['id'] for c in out(resolve(t, 'tool'), 'CAN')] for t in descriptor['tool_ids']}
    w = windows(config)
    t = config['temporal']
    features = {s: o['features'] for s, o in config['observations'].items()}
    artifacts = STAGE_ARTIFACTS + [f"{w[0]['id']}/{f}_{suffix}.tif" for fs in features.values() for f in fs for suffix in FEATURE_LAYERS]
    artifacts += [f"{w[0]['id']}/{name}.tif" for name in DECISION_LAYERS] + [f"{w[0]['id']}/qa.png"]
    return {
        'application': {'id': application, 'title': nodes[application]['title'], 'status': nodes[application]['status']},
        'questions': questions,
        'scientific_methods_for_application': scientific,
        'methods_selected_by_configuration': [{'id': m, 'version': nodes[m]['version'], 'status': nodes[m]['status'],
                                               'workflow_edge': implemented[m]} for m in methods],
        'observation_requirements': observations,
        'datasets_observing_requirements': observable,
        'configured_datasets': configured,
        'access': access,
        'tools': tools,
        'gee_required': 'tool:gee' in descriptor['tool_ids'] or config['execution']['backend'] != 'local-python',
        'workflow': {'id': workflow, 'implementation_version': descriptor['implementation_version'],
                     'declaration_status': descriptor['status'], 'divergences': descriptor['divergences']},
        'configuration': {'backend': config['execution']['backend'], 'crs': config['execution']['crs'],
                          'resolution_m': config['execution']['resolution'], 'tile_size': config['execution']['tile_size'],
                          'temporal_mode': t['mode'], 'alignment': t.get('alignment'), 'window_days': t.get('window_days'),
                          'step_days': t.get('step_days'), 'aggregation': t['aggregation'],
                          'reference_statistic': t.get('reference_statistic', 'period-composites'),
                          'window_count': len(w), 'first_window': w[0], 'last_window': w[-1],
                          'features': features, 'fusion': config['fusion']['mode']},
        'expected_artifacts': artifacts + [f'... same layers for each of {len(w)} windows'],
        'manifest_concept_ids': concept_ids(config, descriptor),
        'knowledge_snapshot': descriptor['knowledge_snapshot'],
        'note': 'Candidate edges are unreviewed proposals. This trace is a semantic plan, not a scientific result.',
    }
