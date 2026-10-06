import logging
from pathlib import Path

import ee

from common import (
    add_ndvi,
    build_cloudmasked_s2_collection,
    configure_logging,
    get_float,
    init_ee,
    load_tiles,
    load_aoi_geometry,
    load_json,
    load_yaml,
    month_date_range,
    output_dir,
    parse_args,
    resolve_output_prefix,
    write_json,
)


def _collection_for_year_month(manifest, aoi, year, month):
    ds = manifest["dataset_ids"]
    threshold = manifest["threshold"]
    start, end = month_date_range(year, month)
    return build_cloudmasked_s2_collection(
        ds["s2_sr"],
        ds["s2_cloud_probability"],
        aoi,
        start,
        end,
        float(threshold["max_cloud_fraction"]),
    ).map(add_ndvi).select("NDVI")


def _merge_reference_ndvi_collections(manifest, aoi, years, month):
    merged = ee.ImageCollection([])
    for y in years:
        merged = merged.merge(_collection_for_year_month(manifest, aoi, y, month))
    return merged


def main() -> None:
    args = parse_args("Compute NDVI anomaly summaries")
    configure_logging()

    manifest = load_json(args.manifest)
    _forest_def = load_yaml(args.forest_def)
    out_prefix = resolve_output_prefix(manifest, args.output_prefix)

    init_ee(args.service_account_key, args.ee_project)
    aoi = load_aoi_geometry(args.aoi_geojson)

    current_year = int(manifest["current_year"])
    current_month = int(manifest["current_month"])
    reference_years = [int(y) for y in manifest["reference_years"]]

    current_ndvi = _collection_for_year_month(manifest, aoi, current_year, current_month).median()

    reference_ndvi = _merge_reference_ndvi_collections(manifest, aoi, reference_years, current_month)

    mu_ref = reference_ndvi.mean().rename("mu_ref")
    sigma_ref = reference_ndvi.reduce(ee.Reducer.stdDev()).rename("sigma_ref")
    anomaly = current_ndvi.subtract(mu_ref).rename("ndvi_anomaly")
    zscore = anomaly.divide(sigma_ref.where(sigma_ref.eq(0), 1e-6)).rename("zscore")

    stats = (
        anomaly.addBands(zscore)
        .reduceRegion(
            reducer=ee.Reducer.mean().combine(reducer2=ee.Reducer.stdDev(), sharedInputs=True),
            geometry=aoi,
            scale=30,
            maxPixels=1e13,
            bestEffort=True,
        )
        .getInfo()
    )

    payload = {
        "run_id": manifest["run_id"],
        "stage": "compute_ndvi_anomaly",
        "current_period": {"year": current_year, "month": current_month},
        "reference_years": reference_years,
        "anomaly_mean": get_float(stats.get("ndvi_anomaly_mean")),
        "anomaly_stddev": get_float(stats.get("ndvi_anomaly_stdDev")),
        "zscore_mean": get_float(stats.get("zscore_mean")),
        "zscore_stddev": get_float(stats.get("zscore_stdDev")),
    }

    tiles = load_tiles(aoi, manifest)
    tile_stats = []
    for tile in tiles:
        tile_geom = ee.Geometry(tile["geometry"])
        tile_region = (
            anomaly.addBands(zscore)
            .reduceRegion(
                reducer=ee.Reducer.mean().combine(reducer2=ee.Reducer.stdDev(), sharedInputs=True),
                geometry=tile_geom,
                scale=30,
                maxPixels=1e13,
                bestEffort=True,
            )
            .getInfo()
        )
        tile_stats.append(
            {
                "tile_id": tile["tile_id"],
                "anomaly_mean": get_float(tile_region.get("ndvi_anomaly_mean")),
                "anomaly_stddev": get_float(tile_region.get("ndvi_anomaly_stdDev")),
                "zscore_mean": get_float(tile_region.get("zscore_mean")),
                "zscore_stddev": get_float(tile_region.get("zscore_stdDev")),
            }
        )

    out_dir = output_dir(out_prefix)
    write_json(Path(out_dir) / "ndvi_anomaly_summary.json", payload)
    write_json(Path(out_dir) / "ndvi_anomaly_tiles.json", {"run_id": manifest["run_id"], "tiles": tile_stats})
    logging.info("Wrote NDVI anomaly summary to %s", Path(out_dir) / "ndvi_anomaly_summary.json")


if __name__ == "__main__":
    main()
