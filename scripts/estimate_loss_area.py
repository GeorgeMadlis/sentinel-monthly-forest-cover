import logging
from pathlib import Path

import ee

from common import (
    add_ndvi,
    build_s1_collection,
    build_cloudmasked_s2_collection,
    clamp01,
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
    s1_confirmation_settings,
    write_json,
)


def _ndvi_collection(manifest, aoi, year, month):
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
        merged = merged.merge(_ndvi_collection(manifest, aoi, y, month))
    return merged


def _build_forest_mask(manifest, forest_def):
    ds = manifest["dataset_ids"]
    current_year = int(manifest["current_year"])
    reference_years = [int(y) for y in manifest["reference_years"]]
    reference_year = max(reference_years)

    tree_thr = int(forest_def["forest_definition"]["treecover2000_threshold_percent"])
    include_loss = bool(forest_def["forest_definition"]["include_loss_up_to_reference_year"])
    max_year = reference_year - 2000

    hansen = ee.Image(ds["forest_mask"])
    canopy = hansen.select("treecover2000").gt(tree_thr)
    no_loss = hansen.select("lossyear").eq(0)
    post_ref_loss = hansen.select("lossyear").gt(max_year)

    if include_loss:
        intact = canopy.And(no_loss.Or(post_ref_loss))
    else:
        # Conservative option: only pixels with no registered loss
        intact = canopy.And(no_loss)

    return intact.rename("forest_mask"), current_year, reference_year


def main() -> None:
    args = parse_args("Estimate disturbed forest area from NDVI anomaly")
    configure_logging()

    manifest = load_json(args.manifest)
    forest_def = load_yaml(args.forest_def)
    out_prefix = resolve_output_prefix(manifest, args.output_prefix)

    init_ee(args.service_account_key, args.ee_project)
    aoi = load_aoi_geometry(args.aoi_geojson)

    current_year = int(manifest["current_year"])
    current_month = int(manifest["current_month"])
    reference_years = [int(y) for y in manifest["reference_years"]]

    current_ndvi = _ndvi_collection(manifest, aoi, current_year, current_month).median()
    reference_ndvi = _merge_reference_ndvi_collections(manifest, aoi, reference_years, current_month)

    mu_ref = reference_ndvi.mean().rename("mu_ref")
    sigma_ref = reference_ndvi.reduce(ee.Reducer.stdDev()).rename("sigma_ref")
    anomaly = current_ndvi.subtract(mu_ref).rename("ndvi_anomaly")

    forest_mask, _, reference_year = _build_forest_mask(manifest, forest_def)
    anomaly_forest = anomaly.updateMask(forest_mask)
    sigma_forest = sigma_ref.updateMask(forest_mask)

    k = float(manifest["threshold"]["k"])
    tau = sigma_forest.multiply(-k).rename("threshold")
    disturbance = anomaly_forest.lt(tau).rename("disturbance")

    s1_cfg = s1_confirmation_settings(manifest)
    s1_confirmation = None
    if s1_cfg["enabled"]:
        ds = manifest["dataset_ids"]
        start_cur, end_cur = month_date_range(current_year, current_month)
        cur_s1 = build_s1_collection(ds["s1_grd_optional"], aoi, start_cur, end_cur).median()

        ref_s1 = ee.ImageCollection([])
        for yr in reference_years:
            start_ref, end_ref = month_date_range(yr, current_month)
            ref_s1 = ref_s1.merge(build_s1_collection(ds["s1_grd_optional"], aoi, start_ref, end_ref))
        ref_s1 = ref_s1.median()

        s1_delta_vv = cur_s1.select("VV").subtract(ref_s1.select("VV"))
        s1_delta_vh = cur_s1.select("VH").subtract(ref_s1.select("VH"))
        vv_drop = s1_delta_vv.lt(s1_cfg["vv_drop_db"]).rename("s1_confirm")
        vh_drop = s1_delta_vh.lt(s1_cfg["vh_drop_db"]).rename("s1_confirm")
        s1_confirmation = vv_drop.And(vh_drop).rename("s1_confirm")
        disturbance = disturbance.updateMask(s1_confirmation)

    min_component_pixels = int(manifest["threshold"].get("min_component_pixels", 1))
    if min_component_pixels > 1:
        cc = disturbance.connectedPixelCount(100, True)
        disturbance = disturbance.updateMask(cc.gte(min_component_pixels))

    tiles = load_tiles(aoi, manifest)
    tile_rows = []
    total_disturbed = 0.0
    conf_sum = 0.0
    valid_sum = 0.0

    for tile in tiles:
        tile_geom = ee.Geometry(tile["geometry"])
        disturbed_ha = (
            disturbance.multiply(ee.Image.pixelArea())
            .reduceRegion(
                reducer=ee.Reducer.sum(),
                geometry=tile_geom,
                scale=30,
                maxPixels=1e13,
                bestEffort=True,
            )
            .get("disturbance")
        )
        disturbed_ha_val = get_float(ee.Number(disturbed_ha).divide(10000).getInfo())

        valid_pixel_ratio = (
            current_ndvi.mask()
            .reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=tile_geom,
                scale=30,
                maxPixels=1e13,
                bestEffort=True,
            )
            .get("NDVI")
        )
        valid_pixel_ratio_val = get_float(ee.Number(valid_pixel_ratio).getInfo())
        cloud_fraction_val = clamp01(1.0 - valid_pixel_ratio_val)

        optical_conf = clamp01(valid_pixel_ratio_val * (1.0 - cloud_fraction_val))
        if s1_cfg["enabled"] and s1_confirmation is not None:
            s1_ratio = (
                s1_confirmation.reduceRegion(
                    reducer=ee.Reducer.mean(),
                    geometry=tile_geom,
                    scale=30,
                    maxPixels=1e13,
                    bestEffort=True,
                ).get("s1_confirm")
            )
            s1_conf = get_float(ee.Number(s1_ratio).getInfo(), default=0.0)
            confidence_score = clamp01(s1_cfg["optical_weight"] * optical_conf + s1_cfg["s1_weight"] * s1_conf)
        else:
            confidence_score = optical_conf

        threshold_mean = tau.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=tile_geom,
            scale=30,
            maxPixels=1e13,
            bestEffort=True,
        ).get("threshold")

        row = {
            "run_id": manifest["run_id"],
            "tile_id": tile["tile_id"],
            "month": f"{current_year}-{current_month:02d}",
            "reference_year": reference_year,
            "disturbed_ha": disturbed_ha_val,
            "valid_pixel_ratio": valid_pixel_ratio_val,
            "cloud_fraction": cloud_fraction_val,
            "confidence_score": confidence_score,
            "threshold_value": get_float(ee.Number(threshold_mean).getInfo()),
            "dataset_versions": manifest["dataset_ids"],
            "s1_confirmation_enabled": s1_cfg["enabled"],
        }
        tile_rows.append(row)
        total_disturbed += disturbed_ha_val
        conf_sum += confidence_score
        valid_sum += valid_pixel_ratio_val

    payload = {
        "run_id": manifest["run_id"],
        "tile_count": len(tile_rows),
        "month": f"{current_year}-{current_month:02d}",
        "disturbed_ha_total": total_disturbed,
        "valid_pixel_ratio_mean": (valid_sum / len(tile_rows)) if tile_rows else 0.0,
        "confidence_score_mean": (conf_sum / len(tile_rows)) if tile_rows else 0.0,
        "dataset_versions": manifest["dataset_ids"],
        "s1_confirmation": s1_cfg,
    }

    out_dir = output_dir(out_prefix)
    write_json(Path(out_dir) / "loss_area_summary.json", payload)
    write_json(Path(out_dir) / "loss_area_tiles.json", {"run_id": manifest["run_id"], "tiles": tile_rows})
    logging.info("Wrote loss area summary to %s", Path(out_dir) / "loss_area_summary.json")


if __name__ == "__main__":
    main()
