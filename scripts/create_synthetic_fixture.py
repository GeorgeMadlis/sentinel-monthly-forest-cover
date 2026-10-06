"""Create a reproducible demonstration without network or satellite credentials."""
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tests.fixtures import create_fixture

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--directory', required=True)
    args = p.parse_args()
    for path in create_fixture(args.directory):
        print(path)
