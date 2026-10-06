"""Run the report stage using local Python geospatial processing."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from forest_change.cli import main

if __name__ == "__main__":
    main("report")
