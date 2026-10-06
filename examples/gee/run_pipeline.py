import argparse
import logging
import subprocess
import sys
from pathlib import Path


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run all monthly forest-loss pipeline stages")
    parser.add_argument("--manifest", required=True, help="Path to run manifest JSON")
    parser.add_argument("--forest-def", required=True, help="Path to forest definition YAML")
    parser.add_argument("--aoi-geojson", required=True, help="Path to AOI GeoJSON")
    parser.add_argument("--output-prefix", default="", help="Optional output prefix override")
    parser.add_argument("--service-account-key", default="", help="Optional GCP service account key JSON")
    parser.add_argument("--ee-project", default="", help="Optional Earth Engine / GCP project ID")
    return parser.parse_args()


def _cmd_for(script_name: str, args: argparse.Namespace) -> list:
    script_path = Path(__file__).parent / script_name
    cmd = [
        sys.executable,
        str(script_path),
        "--manifest",
        args.manifest,
        "--forest-def",
        args.forest_def,
        "--aoi-geojson",
        args.aoi_geojson,
    ]
    if args.output_prefix:
        cmd.extend(["--output-prefix", args.output_prefix])
    if args.service_account_key:
        cmd.extend(["--service-account-key", args.service_account_key])
    if args.ee_project:
        cmd.extend(["--ee-project", args.ee_project])
    return cmd


def main() -> None:
    args = parse_args()
    configure_logging()

    stages = [
        "build_monthly_composites.py",
        "compute_ndvi_anomaly.py",
        "estimate_loss_area.py",
        "export_reporting_artifacts.py",
    ]

    for stage in stages:
        cmd = _cmd_for(stage, args)
        logging.info("Running stage: %s", stage)
        subprocess.run(cmd, check=True)

    logging.info("Pipeline completed successfully")


if __name__ == "__main__":
    main()
