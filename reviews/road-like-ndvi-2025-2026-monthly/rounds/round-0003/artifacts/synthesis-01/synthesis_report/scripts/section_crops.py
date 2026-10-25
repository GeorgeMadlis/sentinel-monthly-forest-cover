#!/usr/bin/env python3
"""synthesis-01 (reprojected to EPSG:3301 at 10 m, nearest neighbour, for ground-true shape): true-colour Sentinel-2 L2A section crops (20 m grid), 2025-06-15 vs 2026-06-20, with ROI outline."""
import json
from pathlib import Path
import numpy as np, rasterio
from shapely.geometry import shape
from shapely.ops import transform
from pyproj import Transformer
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

REPO = Path(__file__).resolve().parents[7]
RUN = REPO / "runs/aoi-s2-jja-2025-2026-calibrated/source_windows"
ROIS = Path(__file__).resolve().parents[3] / "inputs/prior_rois.geojson"
OUT = Path(__file__).resolve().parents[1] / "analysis"
# section centres (lon, lat) and half-size in metres
SECTIONS = {
    "ROI-02-north": ((24.517, 58.567), 1500), "ROI-02-south": ((24.540, 58.522), 1500),
    "ROI-01-west": ((24.640, 58.462), 2500), "ROI-01-middle": ((24.700, 58.492), 2500), "ROI-01-east": ((24.775, 58.523), 2500),
}

from rasterio.warp import reproject, Resampling
from rasterio.transform import from_origin

def rgb_window(period, x, y, half, res=10.0):
    n = int(2 * half / res); dst_tr = from_origin(x - half, y + half, res, res); bands = []
    for b in ("red", "green", "blue"):
        with rasterio.open(RUN / period / f"{b}.tif") as s:
            dst = np.full((n, n), np.nan, "float32")
            reproject(rasterio.band(s, 1), dst, src_nodata=s.nodata, dst_nodata=np.nan, dst_transform=dst_tr,
                      dst_crs="EPSG:3301", resampling=Resampling.nearest)
        bands.append(dst)
    return np.clip(np.dstack(bands) / 0.15, 0, 1) ** 0.8

def main():
    to = Transformer.from_crs(4326, 3301, always_xy=True).transform
    polys = {f["properties"]["id"]: transform(to, shape(f["geometry"])) for f in json.loads(ROIS.read_text())["features"]}
    for name, ((lon, lat), half) in SECTIONS.items():
        x, y = to(lon, lat); poly = polys[name[:6]]
        fig, axes = plt.subplots(1, 2, figsize=(10, 5.2))
        for ax, (p, label) in zip(axes, (("reference", "2025-06-15"), ("target", "2026-06-20"))):
            img = rgb_window(p, x, y, half)
            ax.imshow(np.nan_to_num(img), extent=[x - half, x + half, y - half, y + half], interpolation="nearest")
            xs, ys = poly.exterior.xy; ax.plot(xs, ys, color="yellow", lw=0.8)
            ax.set_xlim(x - half, x + half); ax.set_ylim(y - half, y + half)
            ax.set_title(f"{name}  Sentinel-2 L2A {label}", fontsize=9); ax.set_xticks([]); ax.set_yticks([])
        axes[0].text(0.02, 0.02, f"{2*half/1000:.0f} km x {2*half/1000:.0f} km, EPSG:3301, source 20 m EPSG:6933 grid; yellow = 40 m ROI buffer",
                     transform=axes[0].transAxes, color="white", fontsize=7, backgroundcolor="black")
        fig.tight_layout(); OUT.mkdir(exist_ok=True); fig.savefig(OUT / f"{name}_s2_2025_vs_2026.png", dpi=100); plt.close(fig)

if __name__ == "__main__":
    main()
