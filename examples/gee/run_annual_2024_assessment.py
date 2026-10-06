import argparse
import json
import logging
from pathlib import Path
from typing import Dict, List

import ee
import geemap

from common import (
    add_ndvi,
    build_cloudmasked_s2_collection,
    build_s1_collection,
    configure_logging,
    get_float,
    init_ee,
    load_aoi_geometry,
    load_json,
    load_yaml,
    month_date_range,
    output_dir,
    resolve_output_prefix,
    s1_confirmation_settings,
    write_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compute monthly NDVI disturbance masks for a target year, aggregate annual disturbance, "
            "compare with Hansen loss, and render a final map."
        )
    )
    parser.add_argument("--manifest", required=True, help="Path to run manifest JSON")
    parser.add_argument("--forest-def", required=True, help="Path to forest definition YAML")
    parser.add_argument("--aoi-geojson", required=True, help="Path to AOI GeoJSON")
    parser.add_argument("--output-prefix", default="", help="Optional output prefix override")
    parser.add_argument("--service-account-key", default="", help="Optional path to GCP key JSON")
    parser.add_argument("--ee-project", default="", help="Optional Earth Engine / GCP project ID")
    parser.add_argument(
        "--reference-years",
        default="2021,2022,2023",
        help="Comma-separated reference years (default: 2021,2022,2023)",
    )
    parser.add_argument("--target-year", type=int, default=2024, help="Target year (default: 2024)")
    parser.add_argument(
        "--zoom",
        type=int,
        default=9,
        help="Initial zoom level for final map",
    )
    parser.add_argument(
        "--skip-monthly-mask-exports",
        action="store_true",
        help="Skip exporting monthly disturbance masks as GeoTIFF files.",
    )
    return parser.parse_args()


def _ndvi_collection(manifest: Dict, aoi: ee.Geometry, year: int, month: int) -> ee.ImageCollection:
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


def _merge_reference_ndvi(manifest: Dict, aoi: ee.Geometry, ref_years: List[int], month: int) -> ee.ImageCollection:
    merged = ee.ImageCollection([])
    for year in ref_years:
        merged = merged.merge(_ndvi_collection(manifest, aoi, year, month))
    return merged


def _forest_cover_mask_2023(manifest: Dict, forest_def: Dict) -> ee.Image:
    hansen = ee.Image(manifest["dataset_ids"]["forest_mask"])
    lossyear = hansen.select("lossyear").unmask(0)
    tree_thr = int(forest_def["forest_definition"]["treecover2000_threshold_percent"])
    # Hansen lossyear convention: 1..24 maps to 2001..2024.
    # Forest cover in 2023 = canopy in 2000 with no mapped loss through 2023.
    # That is equivalent to lossyear == 0 (never lost) or lossyear == 24 (lost in 2024).
    return (
        hansen.select("treecover2000").gte(tree_thr)
        .And(lossyear.eq(0).Or(lossyear.eq(24)))
        .rename("forest_cover_2023")
        .selfMask()
    )


def _optional_s1_confirmation(
    manifest: Dict,
    aoi: ee.Geometry,
    reference_years: List[int],
    target_year: int,
    month: int,
) -> ee.Image:
    s1_cfg = s1_confirmation_settings(manifest)
    if not s1_cfg["enabled"]:
        return ee.Image(1).rename("s1_confirm")

    ds = manifest["dataset_ids"]
    start_cur, end_cur = month_date_range(target_year, month)
    cur_s1 = build_s1_collection(ds["s1_grd_optional"], aoi, start_cur, end_cur).median()

    ref_s1 = ee.ImageCollection([])
    for year in reference_years:
        start_ref, end_ref = month_date_range(year, month)
        ref_s1 = ref_s1.merge(build_s1_collection(ds["s1_grd_optional"], aoi, start_ref, end_ref))
    ref_s1 = ref_s1.median()

    return (
        cur_s1.select("VV").subtract(ref_s1.select("VV")).lt(s1_cfg["vv_drop_db"])
        .And(cur_s1.select("VH").subtract(ref_s1.select("VH")).lt(s1_cfg["vh_drop_db"]))
        .rename("s1_confirm")
    )


def _disturbance_for_month(
    manifest: Dict,
    aoi: ee.Geometry,
    forest_cover_2023: ee.Image,
    reference_years: List[int],
    target_year: int,
    month: int,
) -> Dict:
    current_ndvi = _ndvi_collection(manifest, aoi, target_year, month).median()
    reference_ndvi = _merge_reference_ndvi(manifest, aoi, reference_years, month)

    mu_ref = reference_ndvi.mean().rename("mu_ref")
    sigma_ref = reference_ndvi.reduce(ee.Reducer.stdDev()).rename("sigma_ref")
    anomaly = current_ndvi.subtract(mu_ref).rename("ndvi_anomaly")

    k = float(manifest["threshold"]["k"])
    tau = sigma_ref.multiply(-k).rename("threshold")

    disturbance = anomaly.updateMask(forest_cover_2023).lt(tau).rename("disturbance")

    s1_confirm = _optional_s1_confirmation(manifest, aoi, reference_years, target_year, month)
    disturbance = disturbance.updateMask(s1_confirm)

    min_component_pixels = int(manifest["threshold"].get("min_component_pixels", 1))
    if min_component_pixels > 1:
        cc = disturbance.connectedPixelCount(100, True)
        disturbance = disturbance.updateMask(cc.gte(min_component_pixels))

    disturbance = disturbance.unmask(0).rename("disturbance")

    disturbed_ha = (
        disturbance.multiply(ee.Image.pixelArea())
        .reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=aoi,
            scale=30,
            maxPixels=1e13,
            bestEffort=True,
        )
        .get("disturbance")
    )
    disturbed_ha_val = get_float(ee.Number(disturbed_ha).divide(10000).getInfo())

    valid_ratio = (
        current_ndvi.mask()
        .reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=aoi,
            scale=30,
            maxPixels=1e13,
            bestEffort=True,
        )
        .get("NDVI")
    )
    valid_ratio_val = get_float(ee.Number(valid_ratio).getInfo())

    threshold_mean = tau.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=aoi,
        scale=30,
        maxPixels=1e13,
        bestEffort=True,
    ).get("threshold")

    return {
        "month": month,
        "disturbance": disturbance,
        "disturbed_ha": disturbed_ha_val,
        "valid_pixel_ratio": valid_ratio_val,
        "threshold_mean": get_float(ee.Number(threshold_mean).getInfo()),
    }


def _confusion_matrix(
    annual_pred: ee.Image,
    forest_cover_2023: ee.Image,
    hansen_loss_2024: ee.Image,
    aoi: ee.Geometry,
) -> Dict:
    pred = annual_pred.unmask(0).updateMask(forest_cover_2023).rename("pred")
    truth = hansen_loss_2024.unmask(0).updateMask(forest_cover_2023).rename("truth")

    tp = pred.eq(1).And(truth.eq(1)).rename("tp")
    fp = pred.eq(1).And(truth.eq(0)).rename("fp")
    fn = pred.eq(0).And(truth.eq(1)).rename("fn")
    tn = pred.eq(0).And(truth.eq(0)).rename("tn")

    count_image = ee.Image(1).rename("count")

    def _sum_pixels(img: ee.Image, band: str) -> float:
        val = img.reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=aoi,
            scale=30,
            maxPixels=1e13,
            bestEffort=True,
        ).get(band)
        return get_float(ee.Number(val).getInfo())

    def _sum_ha(mask_img: ee.Image, band: str) -> float:
        val = (
            mask_img.multiply(ee.Image.pixelArea())
            .reduceRegion(
                reducer=ee.Reducer.sum(),
                geometry=aoi,
                scale=30,
                maxPixels=1e13,
                bestEffort=True,
            )
            .get(band)
        )
        return get_float(ee.Number(val).divide(10000).getInfo())

    tp_px = _sum_pixels(tp, "tp")
    fp_px = _sum_pixels(fp, "fp")
    fn_px = _sum_pixels(fn, "fn")
    tn_px = _sum_pixels(tn, "tn")

    total_forest_px = _sum_pixels(count_image.updateMask(forest_cover_2023), "count")
    total_forest_ha = _sum_ha(forest_cover_2023.rename("forest_cover_2023"), "forest_cover_2023")

    precision = tp_px / (tp_px + fp_px) if (tp_px + fp_px) else 0.0
    recall = tp_px / (tp_px + fn_px) if (tp_px + fn_px) else 0.0
    accuracy = (tp_px + tn_px) / total_forest_px if total_forest_px else 0.0
    f1 = (2.0 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    return {
        "pixel_counts": {
            "tp": tp_px,
            "fp": fp_px,
            "fn": fn_px,
            "tn": tn_px,
            "total_forest_cover_2023_pixels": total_forest_px,
        },
        "area_ha": {
            "tp": _sum_ha(tp, "tp"),
            "fp": _sum_ha(fp, "fp"),
            "fn": _sum_ha(fn, "fn"),
            "tn": _sum_ha(tn, "tn"),
            "total_forest_cover_2023": total_forest_ha,
        },
        "metrics": {
            "precision": precision,
            "recall": recall,
            "accuracy": accuracy,
            "f1": f1,
        },
    }


def _render_final_map(
    out_prefix: str,
    aoi: ee.Geometry,
    zoom: int,
    annual_rgb_2024: ee.Image,
    forest_cover_2023: ee.Image,
    hansen_loss_2024: ee.Image,
    annual_disturbance: ee.Image,
) -> None:
    m = geemap.Map(add_google_map=True, basemap="SATELLITE")
    m.centerObject(aoi, zoom)

    m.addLayer(annual_rgb_2024.clip(aoi), {"min": 0.0, "max": 0.3}, "Sentinel-2 RGB 2024")
    m.addLayer(
        forest_cover_2023.clip(aoi),
        {"palette": ["1f7a1f"]},
        "Hansen Forest Cover 2023",
        True,
    )
    m.addLayer(
        hansen_loss_2024.selfMask().clip(aoi),
        {"palette": ["ffd11a"]},
        "Hansen Forest Loss 2024",
        True,
    )
    m.addLayer(
        annual_disturbance.selfMask().clip(aoi),
        {"palette": ["ff1a1a"]},
        "NDVI Disturbance Loss 2024 (Any Month)",
        True,
    )

    out_path = Path(out_prefix) / "final_map.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    m.to_html(filename=str(out_path), title="Annual NDVI Disturbance vs Hansen (2024)", width="100%", height="900px")


def main() -> None:
    args = parse_args()
    configure_logging()

    manifest = load_json(args.manifest)
    forest_def = load_yaml(args.forest_def)

    ref_years = [int(x.strip()) for x in args.reference_years.split(",") if x.strip()]
    if not ref_years:
        raise ValueError("reference-years must contain at least one year")

    default_prefix = f"{manifest['output']['prefix']}-annual-{args.target_year}"
    out_prefix = resolve_output_prefix(manifest, args.output_prefix) if args.output_prefix else default_prefix

    init_ee(args.service_account_key, args.ee_project)
    aoi = load_aoi_geometry(args.aoi_geojson)

    out_dir = output_dir(out_prefix)
    monthly_dir = out_dir / "monthly_masks"
    monthly_dir.mkdir(parents=True, exist_ok=True)
    export_region = aoi.bounds(1).getInfo()["coordinates"]

    forest_cover_2023 = _forest_cover_mask_2023(manifest, forest_def)
    hansen = ee.Image(manifest["dataset_ids"]["forest_mask"])
    hansen_loss_2024 = (
        hansen.select("lossyear").unmask(0).eq(24).updateMask(forest_cover_2023).rename("hansen_loss_2024")
    )

    monthly_results = []
    monthly_disturbance_images = []

    for month in range(1, 13):
        logging.info("Processing target year %s month %02d", args.target_year, month)
        month_result = _disturbance_for_month(
            manifest,
            aoi,
            forest_cover_2023,
            ref_years,
            args.target_year,
            month,
        )
        month_disturbance = month_result.pop("disturbance")

        month_name = f"{args.target_year}-{month:02d}"
        monthly_results.append({"month": month_name, **month_result})
        # Keep a homogeneous band schema for ImageCollection max().
        monthly_disturbance_images.append(month_disturbance.rename("disturbance"))

        if not args.skip_monthly_mask_exports:
            out_tif = monthly_dir / f"disturbance_mask_{month_name}.tif"
            geemap.ee_export_image(
                month_disturbance.unmask(0).clip(aoi).toByte(),
                filename=str(out_tif),
                scale=30,
                region=export_region,
                file_per_band=False,
            )

    annual_disturbance = ee.ImageCollection(monthly_disturbance_images).max().rename("annual_ndvi_disturbance")

    confusion = _confusion_matrix(annual_disturbance, forest_cover_2023, hansen_loss_2024, aoi)

    annual_start, annual_end = month_date_range(args.target_year, 1)[0], month_date_range(args.target_year, 12)[1]
    annual_rgb_2024 = (
        build_cloudmasked_s2_collection(
            manifest["dataset_ids"]["s2_sr"],
            manifest["dataset_ids"]["s2_cloud_probability"],
            aoi,
            annual_start,
            annual_end,
            float(manifest["threshold"]["max_cloud_fraction"]),
        )
        .select(["B4", "B3", "B2"])
        .median()
    )

    _render_final_map(
        out_prefix,
        aoi,
        args.zoom,
        annual_rgb_2024,
        forest_cover_2023,
        hansen_loss_2024,
        annual_disturbance,
    )

    annual_disturbed_ha = get_float(
        ee.Number(
            annual_disturbance.multiply(ee.Image.pixelArea())
            .reduceRegion(
                reducer=ee.Reducer.sum(),
                geometry=aoi,
                scale=30,
                maxPixels=1e13,
                bestEffort=True,
            )
            .get("annual_ndvi_disturbance")
        )
        .divide(10000)
        .getInfo()
    )

    summary = {
        "run_id": manifest.get("run_id", "run"),
        "task": "annual_12_month_ndvi_disturbance_vs_hansen",
        "target_year": args.target_year,
        "reference_years": ref_years,
        "monthly_results": monthly_results,
        "annual_any_month_disturbed_ha": annual_disturbed_ha,
        "comparison_domain": "Hansen forest cover in 2023",
        "confusion_matrix": confusion,
        "outputs": {
            "monthly_masks_dir": str(monthly_dir),
            "confusion_matrix_json": str(out_dir / "confusion_matrix_2024.json"),
            "annual_summary_json": str(out_dir / "annual_disturbance_summary_2024.json"),
            "final_map_html": str(out_dir / "final_map.html"),
        },
    }

    write_json(out_dir / "confusion_matrix_2024.json", confusion)
    write_json(out_dir / "annual_disturbance_summary_2024.json", summary)

    # Store a lightweight annual mask descriptor for reproducibility.
    annual_mask_descriptor = {
        "image_band": "annual_ndvi_disturbance",
        "definition": "pixel is 1 if monthly disturbance == 1 in any month of target year",
        "target_year": args.target_year,
        "reference_years": ref_years,
    }
    write_json(out_dir / "annual_disturbance_mask_2024.json", annual_mask_descriptor)

    logging.info("Wrote annual summary to %s", out_dir / "annual_disturbance_summary_2024.json")
    logging.info("Wrote confusion matrix to %s", out_dir / "confusion_matrix_2024.json")
    logging.info("Wrote final map to %s", out_dir / "final_map.html")


if __name__ == "__main__":
    main()
