import argparse
import calendar
import json
import logging
import os
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Tuple

import ee
import yaml


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_yaml(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    ensure_parent(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)


def write_text(path: Path, text: str) -> None:
    ensure_parent(path)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def init_ee(service_account_key: str = "", ee_project: str = "") -> None:
    key = service_account_key or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
    project = ee_project or os.environ.get("EE_PROJECT", "")
    if key:
        credentials = ee.ServiceAccountCredentials(email=None, key_file=key)
        if project:
            ee.Initialize(credentials, project=project)
        else:
            ee.Initialize(credentials)
    else:
        if project:
            ee.Initialize(project=project)
        else:
            ee.Initialize()


def month_date_range(year: int, month: int) -> Tuple[str, str]:
    last_day = calendar.monthrange(year, month)[1]
    start = date(year, month, 1).isoformat()
    end = date(year, month, last_day).isoformat()
    return start, end


def parse_args(description: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--manifest", required=True, help="Path to run manifest JSON")
    parser.add_argument("--forest-def", required=True, help="Path to forest definition YAML")
    parser.add_argument("--aoi-geojson", required=True, help="Path to AOI GeoJSON")
    parser.add_argument(
        "--output-prefix",
        default="",
        help="Optional override for output prefix directory",
    )
    parser.add_argument(
        "--service-account-key",
        default="",
        help="Optional path to GCP service account key JSON",
    )
    parser.add_argument(
        "--ee-project",
        default="",
        help="Optional Earth Engine / Google Cloud project ID",
    )
    return parser.parse_args()


def resolve_output_prefix(manifest: Dict[str, Any], cli_output_prefix: str) -> str:
    if cli_output_prefix:
        return cli_output_prefix
    return manifest["output"]["prefix"]


def load_aoi_geometry(aoi_geojson_path: str) -> ee.Geometry:
    with open(aoi_geojson_path, "r", encoding="utf-8") as f:
        gj = json.load(f)

    if gj.get("type") == "FeatureCollection":
        features = gj.get("features", [])
        if not features:
            raise ValueError("AOI GeoJSON FeatureCollection has no features")
        geom = features[0].get("geometry")
    elif gj.get("type") == "Feature":
        geom = gj.get("geometry")
    else:
        geom = gj

    if not geom:
        raise ValueError("AOI GeoJSON does not contain geometry")

    return ee.Geometry(geom)


def add_ndvi(image: ee.Image) -> ee.Image:
    ndvi = image.normalizedDifference(["B8", "B4"]).rename("NDVI")
    return image.addBands(ndvi)


def _mask_joined_clouds(image: ee.Image, threshold_pct: float) -> ee.Image:
    cloud_img = ee.Image(image.get("cloud_mask"))
    cloud_mask = cloud_img.select("probability").lt(threshold_pct)
    return (
        image.updateMask(cloud_mask)
        .divide(10000)
        .copyProperties(image, ["system:time_start", "system:index"])
    )


def build_cloudmasked_s2_collection(
    s2_sr_id: str,
    s2_cloud_id: str,
    aoi: ee.Geometry,
    start_date: str,
    end_date: str,
    max_cloud_fraction: float,
) -> ee.ImageCollection:
    threshold_pct = max_cloud_fraction * 100.0
    sr = (
        ee.ImageCollection(s2_sr_id)
        .filterBounds(aoi)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", threshold_pct))
    )
    clouds = ee.ImageCollection(s2_cloud_id).filterBounds(aoi).filterDate(start_date, end_date)
    joined = ee.Join.saveFirst("cloud_mask").apply(
        primary=sr,
        secondary=clouds,
        condition=ee.Filter.equals(leftField="system:index", rightField="system:index"),
    )
    return ee.ImageCollection(joined).map(lambda i: _mask_joined_clouds(ee.Image(i), threshold_pct))


def get_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def output_dir(base_prefix: str) -> Path:
    path = Path(base_prefix)
    path.mkdir(parents=True, exist_ok=True)
    return path


def summarize_collection(collection: ee.ImageCollection, label: str) -> Dict[str, Any]:
    return {
        "label": label,
        "count": int(collection.size().getInfo()),
    }


def load_tiles(aoi: ee.Geometry, manifest: Dict[str, Any]) -> List[Dict[str, Any]]:
    tiling_cfg = manifest.get("tiling", {})
    tile_size_deg = float(tiling_cfg.get("tile_size_degrees", 0))

    if tile_size_deg <= 0:
        return [
            {
                "tile_id": f"{manifest.get('aoi_id', 'aoi')}_0001",
                "geometry": aoi.getInfo(),
            }
        ]

    bbox = ee.Geometry(aoi.bounds(1)).coordinates().getInfo()[0]
    lons = [p[0] for p in bbox]
    lats = [p[1] for p in bbox]
    min_lon, max_lon = min(lons), max(lons)
    min_lat, max_lat = min(lats), max(lats)

    tiles: List[Dict[str, Any]] = []
    row = 0
    lat = min_lat
    while lat < max_lat:
        col = 0
        lon = min_lon
        while lon < max_lon:
            cell = ee.Geometry.Rectangle(
                [lon, lat, min(lon + tile_size_deg, max_lon), min(lat + tile_size_deg, max_lat)],
                proj=None,
                geodesic=False,
            )
            inter = ee.Geometry(cell.intersection(aoi, ee.ErrorMargin(1)))
            if float(inter.area(1).getInfo()) > 0:
                tiles.append(
                    {
                        "tile_id": f"{manifest.get('aoi_id', 'aoi')}_{row:03d}_{col:03d}",
                        "geometry": inter.getInfo(),
                    }
                )
            col += 1
            lon += tile_size_deg
        row += 1
        lat += tile_size_deg

    if not tiles:
        raise ValueError("No non-empty tiles were generated for the AOI")
    return tiles


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def s1_confirmation_settings(manifest: Dict[str, Any]) -> Dict[str, Any]:
    cfg = manifest.get("s1_confirmation", {})
    return {
        "enabled": bool(cfg.get("enabled", False)),
        "vv_drop_db": float(cfg.get("vv_drop_db", -1.5)),
        "vh_drop_db": float(cfg.get("vh_drop_db", -1.0)),
        "optical_weight": float(cfg.get("optical_weight", 0.7)),
        "s1_weight": float(cfg.get("s1_weight", 0.3)),
    }


def build_s1_collection(
    s1_id: str,
    aoi: ee.Geometry,
    start_date: str,
    end_date: str,
) -> ee.ImageCollection:
    return (
        ee.ImageCollection(s1_id)
        .filterBounds(aoi)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.eq("instrumentMode", "IW"))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH"))
        .select(["VV", "VH"])
    )
