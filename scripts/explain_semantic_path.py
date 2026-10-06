"""Print the Forest Cover Lab reasoning path for a workflow configuration (no data access)."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from forest_change.config import normalize
from forest_change.evidence import load
from forest_change.semantics import explain

ROOT = Path(__file__).resolve().parents[1]

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config', required=True, help='Schema 2.0 workflow YAML/JSON')
    p.add_argument('--lab', default=str(ROOT.parent / 'forest-cover-lab'), help='Forest Cover Lab checkout at the pinned revision')
    args = p.parse_args()
    graph = json.loads((Path(args.lab) / 'graph/generated/knowledge.json').read_text())
    # Validate the configuration without resolving local paths or opening any raster/catalogue.
    config = normalize(load(args.config))
    print(json.dumps(explain(config, load(ROOT / 'workflow.yaml'), graph), indent=2, sort_keys=True))
