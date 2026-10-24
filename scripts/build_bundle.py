#!/usr/bin/env python3
"""Package curated local planning inputs. No download, analysis or publication."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from forest_change.bundle import build_bundle, verify_bundle


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--review', type=Path)
    p.add_argument('--destination', type=Path)
    p.add_argument('--verify', type=Path, help='Verify an existing or ZIP-extracted bundle')
    a = p.parse_args()
    if a.verify:
        if a.review or a.destination:
            p.error('--verify cannot be combined with build arguments')
        result = verify_bundle(a.verify)
    else:
        if not a.review or not a.destination:
            p.error('--review and --destination are required')
        result = build_bundle(a.review, a.destination)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
