import logging
from pathlib import Path

import ee

from common import (
    build_cloudmasked_s2_collection,
    configure_logging,
    init_ee,
    load_tiles,
    load_aoi_geometry,
    load_json,
    load_yaml,
    month_date_range,
    output_dir,
    parse_args,
    resolve_output_prefix,
    summarize_collection,
    write_json,
)


def main() -> None:
    args = parse_args("Build monthly reference/current composites metadata")
    configure_logging()

    manifest = load_json(args.manifest)
    _forest_def = load_yaml(args.forest_def)
    out_prefix = resolve_output_prefix(manifest, args.output_prefix)

    init_ee(args.service_account_key, args.ee_project)
    aoi = load_aoi_geometry(args.aoi_geojson)

    ds = manifest["dataset_ids"]
    threshold = manifest["threshold"]
    current_year = int(manifest["current_year"])
    current_month = int(manifest["current_month"])
    reference_years = [int(y) for y in manifest["reference_years"]]

    start_cur, end_cur = month_date_range(current_year, current_month)
    current_collection = build_cloudmasked_s2_collection(
        ds["s2_sr"],
        ds["s2_cloud_probability"],
        aoi,
        start_cur,
        end_cur,
        float(threshold["max_cloud_fraction"]),
    )

    reference_counts = []
    for yr in reference_years:
        start_ref, end_ref = month_date_range(yr, current_month)
        ref_collection = build_cloudmasked_s2_collection(
            ds["s2_sr"],
            ds["s2_cloud_probability"],
            aoi,
            start_ref,
            end_ref,
            float(threshold["max_cloud_fraction"]),
        )
        reference_counts.append(summarize_collection(ref_collection, f"{yr}-{current_month:02d}"))

    tiles = load_tiles(aoi, manifest)
    per_tile = []
    for tile in tiles:
        tile_geom = ee.Geometry(tile["geometry"])
        tile_refs = []
        for yr in reference_years:
            start_ref, end_ref = month_date_range(yr, current_month)
            ref_count = (
                build_cloudmasked_s2_collection(
                    ds["s2_sr"],
                    ds["s2_cloud_probability"],
                    tile_geom,
                    start_ref,
                    end_ref,
                    float(threshold["max_cloud_fraction"]),
                )
                .size()
                .getInfo()
            )
            tile_refs.append({"year": yr, "count": int(ref_count)})

        cur_count = int(current_collection.filterBounds(tile_geom).size().getInfo())
        per_tile.append({"tile_id": tile["tile_id"], "current_count": cur_count, "reference_counts": tile_refs})

    payload = {
        "run_id": manifest["run_id"],
        "stage": "build_monthly_composites",
        "current_period": {"year": current_year, "month": current_month, "start": start_cur, "end": end_cur},
        "reference_years": reference_years,
        "reference_collections": reference_counts,
        "current_collection": summarize_collection(current_collection, f"{current_year}-{current_month:02d}"),
        "dataset_ids": ds,
        "tile_count": len(tiles),
    }

    out_dir = output_dir(out_prefix)
    write_json(Path(out_dir) / "composites_metadata.json", payload)
    write_json(Path(out_dir) / "composites_tiles.json", {"run_id": manifest["run_id"], "tiles": per_tile})
    logging.info("Wrote composites metadata to %s", Path(out_dir) / "composites_metadata.json")


if __name__ == "__main__":
    main()
