#!/usr/bin/env python3
"""Validate this checkout's review rounds using an explicitly selected Lab checkout."""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lab", required=True, type=Path)
    args = parser.parse_args()
    lab = args.lab.resolve()
    validator = lab / "agent_harness/scripts/validate_round.py"
    if not validator.is_file():
        parser.error("--lab must contain agent_harness/scripts/validate_round.py")
    return subprocess.run(
        [sys.executable, str(validator), "--lab", str(lab), "--root", str(ROOT)],
        check=False,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
