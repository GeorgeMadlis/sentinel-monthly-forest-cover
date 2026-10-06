import csv
import json
import logging
from pathlib import Path

from common import (
    configure_logging,
    load_json,
    load_yaml,
    output_dir,
    parse_args,
    resolve_output_prefix,
    write_json,
    write_text,
)


def _load_aoi_feature(aoi_geojson_path: str):
    with open(aoi_geojson_path, "r", encoding="utf-8") as f:
        gj = json.load(f)

    if gj.get("type") == "FeatureCollection":
        features = gj.get("features", [])
        if not features:
            raise ValueError("AOI GeoJSON FeatureCollection has no features")
        return features[0]

    if gj.get("type") == "Feature":
        return gj

    return {"type": "Feature", "geometry": gj, "properties": {}}


def main() -> None:
    args = parse_args("Export CSV, GeoJSON, and markdown reporting artifacts")
    configure_logging()

    manifest = load_json(args.manifest)
    _forest_def = load_yaml(args.forest_def)
    out_prefix = resolve_output_prefix(manifest, args.output_prefix)
    out_dir = output_dir(out_prefix)

    summary_path = Path(out_dir) / "loss_area_summary.json"
    tiles_path = Path(out_dir) / "loss_area_tiles.json"
    if not summary_path.exists() or not tiles_path.exists():
        raise FileNotFoundError(
            f"Expected files {summary_path} and {tiles_path}. Run estimate_loss_area.py first."
        )

    summary = load_json(str(summary_path))
    tile_rows = load_json(str(tiles_path)).get("tiles", [])

    csv_path = Path(out_dir) / "loss_area_tiles.csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        if tile_rows:
            fieldnames = list(tile_rows[0].keys())
        else:
            fieldnames = ["run_id", "tile_id", "month", "disturbed_ha", "confidence_score"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in tile_rows:
            writer.writerow(row)

    aoi_feature = _load_aoi_feature(args.aoi_geojson)
    # Per-tile geometry is not persisted in this stage; attach rows to AOI feature as compact artifacts.
    feature = {
        "type": "Feature",
        "geometry": aoi_feature["geometry"],
        "properties": {
            "run_id": summary["run_id"],
            "month": summary["month"],
            "disturbed_ha_total": summary["disturbed_ha_total"],
            "confidence_score_mean": summary["confidence_score_mean"],
            "tile_count": summary["tile_count"],
        },
    }
    geojson_payload = {"type": "FeatureCollection", "features": [feature]}
    write_json(Path(out_dir) / "loss_area_summary.geojson", geojson_payload)

    report_md = "\n".join(
        [
            "# Monthly Disturbance Report",
            "",
            f"- run_id: {summary['run_id']}",
            f"- month: {summary['month']}",
            f"- tile_count: {summary['tile_count']}",
            f"- disturbed_ha_total: {summary['disturbed_ha_total']}",
            f"- valid_pixel_ratio_mean: {summary['valid_pixel_ratio_mean']}",
            f"- confidence_score_mean: {summary['confidence_score_mean']}",
            "",
            "## Notes",
            "",
            "Results are monthly disturbance confirmations and should be reconciled with annual reference products for final reporting.",
        ]
    )
    write_text(Path(out_dir) / "report.md", report_md)

    write_json(Path(out_dir) / "loss_area_tiles_report.json", {"run_id": summary["run_id"], "tiles": tile_rows})

    logging.info("Wrote reporting artifacts to %s", out_dir)


if __name__ == "__main__":
    main()
