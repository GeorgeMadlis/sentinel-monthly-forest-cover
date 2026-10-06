import argparse
import logging
from pathlib import Path

import ee
import geemap

from common import (
    add_ndvi,
    build_cloudmasked_s2_collection,
    build_s1_collection,
    init_ee,
    load_aoi_geometry,
    load_json,
    load_yaml,
    month_date_range,
    resolve_output_prefix,
    s1_confirmation_settings,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render final monthly forest-loss map")
    parser.add_argument("--manifest", required=True, help="Path to run manifest JSON")
    parser.add_argument("--forest-def", required=True, help="Path to forest definition YAML")
    parser.add_argument("--aoi-geojson", required=True, help="Path to AOI GeoJSON")
    parser.add_argument("--output-prefix", default="", help="Optional output prefix override")
    parser.add_argument("--service-account-key", default="", help="Optional path to GCP key")
    parser.add_argument("--ee-project", default="", help="Optional Earth Engine / GCP project ID")
    parser.add_argument("--zoom", type=int, default=9, help="Initial map zoom")
    return parser.parse_args()


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
    ).map(add_ndvi)


def _merge_reference_ndvi_collections(manifest, aoi, years, month):
    merged = ee.ImageCollection([])
    for y in years:
        merged = merged.merge(_ndvi_collection(manifest, aoi, y, month).select("NDVI"))
    return merged


def _forest_cover_2024(hansen: ee.Image, tree_cover_threshold: int) -> ee.Image:
    # Approximate cover in 2024 as canopy in 2000 with no mapped loss through 2024.
    return (
        hansen.select("treecover2000").gte(tree_cover_threshold)
        .And(hansen.select("lossyear").eq(0).Or(hansen.select("lossyear").gt(24)))
        .selfMask()
        .rename("forest_cover_2024")
    )


def _ndvi_disturbance_mask(manifest, forest_def, aoi):
    current_year = int(manifest["current_year"])
    current_month = int(manifest["current_month"])
    reference_years = [int(y) for y in manifest["reference_years"]]

    current_ndvi = _ndvi_collection(manifest, aoi, current_year, current_month).select("NDVI").median()
    reference_ndvi = _merge_reference_ndvi_collections(manifest, aoi, reference_years, current_month)

    mu_ref = reference_ndvi.mean()
    sigma_ref = reference_ndvi.reduce(ee.Reducer.stdDev()).rename("sigma_ref")
    anomaly = current_ndvi.subtract(mu_ref).rename("ndvi_anomaly")

    hansen = ee.Image(manifest["dataset_ids"]["forest_mask"])
    tree_thr = int(forest_def["forest_definition"]["treecover2000_threshold_percent"])
    reference_year = max(reference_years)
    max_year = reference_year - 2000

    forest_mask = (
        hansen.select("treecover2000").gte(tree_thr)
        .And(hansen.select("lossyear").eq(0).Or(hansen.select("lossyear").gt(max_year)))
        .selfMask()
    )

    k = float(manifest["threshold"]["k"])
    tau = sigma_ref.multiply(-k)
    disturbance = anomaly.updateMask(forest_mask).lt(tau).rename("ndvi_disturbance")

    min_component_pixels = int(manifest["threshold"].get("min_component_pixels", 1))
    if min_component_pixels > 1:
        cc = disturbance.connectedPixelCount(100, True)
        disturbance = disturbance.updateMask(cc.gte(min_component_pixels))

    s1_cfg = s1_confirmation_settings(manifest)
    if s1_cfg["enabled"]:
        ds = manifest["dataset_ids"]
        start_cur, end_cur = month_date_range(current_year, current_month)
        cur_s1 = build_s1_collection(ds["s1_grd_optional"], aoi, start_cur, end_cur).median()

        ref_s1 = ee.ImageCollection([])
        for yr in reference_years:
            start_ref, end_ref = month_date_range(yr, current_month)
            ref_s1 = ref_s1.merge(build_s1_collection(ds["s1_grd_optional"], aoi, start_ref, end_ref))
        ref_s1 = ref_s1.median()

        s1_confirmation = (
            cur_s1.select("VV").subtract(ref_s1.select("VV")).lt(s1_cfg["vv_drop_db"])
            .And(cur_s1.select("VH").subtract(ref_s1.select("VH")).lt(s1_cfg["vh_drop_db"]))
            .rename("s1_confirm")
        )
        disturbance = disturbance.updateMask(s1_confirmation)

    return disturbance.selfMask()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = parse_args()

    manifest = load_json(args.manifest)
    forest_def = load_yaml(args.forest_def)
    out_prefix = resolve_output_prefix(manifest, args.output_prefix)

    init_ee(args.service_account_key, args.ee_project)
    aoi = load_aoi_geometry(args.aoi_geojson)

    current_year = int(manifest["current_year"])
    current_month = int(manifest["current_month"])

    s2_rgb = _ndvi_collection(manifest, aoi, current_year, current_month).select(["B4", "B3", "B2"]).median()

    hansen = ee.Image(manifest["dataset_ids"]["forest_mask"])
    tree_thr = int(forest_def["forest_definition"]["treecover2000_threshold_percent"])
    hansen_cover_2024 = _forest_cover_2024(hansen, tree_thr)
    hansen_loss_2024 = hansen.select("lossyear").eq(24).selfMask().rename("hansen_loss_2024")

    ndvi_disturbance = _ndvi_disturbance_mask(manifest, forest_def, aoi)

    m = geemap.Map()
    m.centerObject(aoi, args.zoom)
    m.add_basemap("Esri.WorldImagery")
    m.addLayer(s2_rgb.clip(aoi), {"min": 0.0, "max": 0.3}, "Sentinel-2 RGB")
    m.addLayer(
        hansen_cover_2024.clip(aoi),
        {"palette": ["1f7a1f"]},
        "Hansen Forest Cover 2024",
        True,
    )
    m.addLayer(
        hansen_loss_2024.clip(aoi),
        {"palette": ["ffd11a"]},
        "Hansen Forest Loss 2024",
        True,
    )
    m.addLayer(
        ndvi_disturbance.clip(aoi),
        {"palette": ["ff1a1a"]},
        "NDVI Disturbance Loss",
        True,
    )

    out_path = Path(out_prefix) / "final_map.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    m.to_html(filename=str(out_path), title="Monthly Forest Loss Final Map", width="100%", height="900px")

    logging.info("Final map written to %s", out_path)


if __name__ == "__main__":
    main()
