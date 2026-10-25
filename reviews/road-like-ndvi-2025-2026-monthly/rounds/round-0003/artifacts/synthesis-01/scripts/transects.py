#!/usr/bin/env python3
"""synthesis-01 diagnostic: NDVI cross-profiles along ROI corridors, 2025-06-15 vs 2026-06-20.

Diagnostic run configuration only (not a Lab threshold): low-NDVI band = contiguous pixels
with NDVI < LOW around the profile minimum within +/-CENTRE_M of the sampled centreline.
Width resolution is limited by the 20 m grid and mixed pixels. Geometry is built in EPSG:3301
(conformal, ground metres); the EPSG:6933 equal-area raster is sampled by coordinate transform,
because a 20 m EPSG:6933 cell is about 12 m (E-W) x 33 m (N-S) on the ground at 58.5 N.
"""
import csv, hashlib, json, sys
from pathlib import Path
import numpy as np, rasterio
from shapely.geometry import shape, LineString, Point
from shapely.ops import transform
from pyproj import Transformer
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

REPO = Path(__file__).resolve().parents[7]
RUN = REPO / "runs/aoi-s2-jja-2025-2026-calibrated/source_windows"
ROIS = Path(__file__).resolve().parents[3] / "inputs/prior_rois.geojson"
OUT = Path(__file__).resolve().parents[1] / "analysis"
LOW, CONTRAST, CENTRE_M, HALF_M, STEP_M, STATION_M = 0.35, 0.15, 150.0, 250.0, 10.0, 250.0
VALID_SCL = {4, 5, 6, 7}

def load(period):
    out = {}
    for b in ("red", "nir", "scl"):
        with rasterio.open(RUN / period / f"{b}.tif") as s:
            out[b] = s.read(1); tr = s.transform; nod = s.nodata
    red, nir, scl = out["red"], out["nir"], out["scl"]
    ok = (red != nod) & (nir != nod) & np.isin(scl, list(VALID_SCL)) & ((red + nir) > 0)
    ndvi = np.full(red.shape, np.nan, "float32")
    ndvi[ok] = (nir[ok] - red[ok]) / (nir[ok] + red[ok])
    return ndvi, tr

def centreline(poly):
    """Midline of the thin buffer: average each vertex of one side with its nearest point on the other side."""
    ring = list(poly.simplify(10).exterior.coords)[:-1]
    n = len(ring)
    i, j = max(((i, j) for i in range(n) for j in range(i + 1, n)), key=lambda ij: Point(ring[ij[0]]).distance(Point(ring[ij[1]])))
    a, b = LineString(ring[i : j + 1]), LineString(ring[j:] + ring[: i + 1])
    pts = [a.interpolate(d) for d in np.arange(0, a.length, 50.0)]
    mid = [((p.x + b.interpolate(b.project(p)).x) / 2, (p.y + b.interpolate(b.project(p)).y) / 2) for p in pts]
    return LineString(mid)

TO_RASTER = Transformer.from_crs(3301, 6933, always_xy=True)

def sample(arr, tr, x, y):
    x, y = TO_RASTER.transform(x, y)
    c, r = ~tr * (x, y); r, c = int(np.floor(r)), int(np.floor(c))
    if 0 <= r < arr.shape[0] and 0 <= c < arr.shape[1]: return float(arr[r, c])
    return float("nan")

def band_width(offsets, prof, limit=None):
    centre = np.abs(offsets) <= CENTRE_M
    if limit is None: limit = LOW
    if np.all(np.isnan(prof[centre])): return float("nan"), float("nan")
    i0 = np.where(centre)[0][np.nanargmin(prof[centre])]
    if not prof[i0] < limit: return 0.0, float(prof[i0])
    lo = hi = i0
    while lo > 0 and prof[lo - 1] < limit: lo -= 1
    while hi < len(prof) - 1 and prof[hi + 1] < limit: hi += 1
    return float((hi - lo + 1) * STEP_M), float(prof[i0])

def main():
    ref, tr = load("reference"); tgt, tr2 = load("target"); assert tr == tr2
    to = Transformer.from_crs(4326, 3301, always_xy=True).transform
    back = Transformer.from_crs(3301, 4326, always_xy=True).transform
    feats = json.loads(ROIS.read_text())["features"]
    rows, offsets = [], np.arange(-HALF_M, HALF_M + STEP_M, STEP_M)
    fig, axes = plt.subplots(2, 1, figsize=(9, 7))
    for ax, f in zip(axes, [f for f in feats if f["properties"]["id"].startswith("ROI")]):
        rid = f["properties"]["id"]; line = centreline(transform(to, shape(f["geometry"])))
        widths = {"2025": [], "2026": []}; heat = {"2025": [], "2026": []}
        for k, d in enumerate(np.arange(STATION_M / 2, line.length, STATION_M)):
            p = line.interpolate(d); q = line.interpolate(min(d + 5, line.length)); p0 = line.interpolate(max(d - 5, 0))
            dx, dy = q.x - p0.x, q.y - p0.y; n = np.hypot(dx, dy); nx, ny = -dy / n, dx / n
            prof = {y: np.array([sample(a, tr, p.x + o * nx, p.y + o * ny) for o in offsets]) for y, a in (("2025", ref), ("2026", tgt))}
            w25, m25 = band_width(offsets, prof["2025"]); w26, m26 = band_width(offsets, prof["2026"])
            c25, _ = band_width(offsets, prof["2025"], np.nanmedian(prof["2025"]) - CONTRAST)
            c26, _ = band_width(offsets, prof["2026"], np.nanmedian(prof["2026"]) - CONTRAST)
            heat["2025"].append(prof["2025"]); heat["2026"].append(prof["2026"])
            lon, lat = back(p.x, p.y)
            rows.append(dict(roi_id=rid, station=k, chainage_m=round(d), lon=round(lon, 5), lat=round(lat, 5),
                             low_band_width_2025_m=w25, low_band_width_2026_m=w26, contrast_band_width_2025_m=c25, contrast_band_width_2026_m=c26, min_ndvi_2025=round(m25, 3), min_ndvi_2026=round(m26, 3)))
            widths["2025"].append(w25); widths["2026"].append(w26)
        hf, hx = plt.subplots(1, 2, figsize=(9, 4.6), sharey=True)
        for axh, y in zip(hx, ("2025", "2026")):
            im = axh.imshow(np.array(heat[y]), vmin=0, vmax=0.9, cmap="viridis", aspect="auto",
                            extent=[-HALF_M, HALF_M, line.length / 1000, 0])
            axh.set_title(f"{rid}, {'2025-06-15' if y == '2025' else '2026-06-20'}", fontsize=10)
            axh.set_xlabel("offset from sampled centreline (m)")
        hx[0].set_ylabel("distance along centreline (km)"); hf.colorbar(im, ax=hx, label="NDVI")
        OUT.mkdir(exist_ok=True); hf.savefig(OUT / f"{rid}_ndvi_cross_profiles.png", dpi=110); plt.close(hf)
        ch = [r["chainage_m"] / 1000 for r in rows if r["roi_id"] == rid]
        ax.plot(ch, widths["2025"], "o-", label="2025-06-15", color="#2b6cb0")
        ax.plot(ch, widths["2026"], "s-", label="2026-06-20", color="#c05621")
        ax.set_title(f"{rid}: width of low-NDVI band (NDVI < {LOW}) across sampled centreline")
        ax.set_xlabel("distance along sampled centreline (km)"); ax.set_ylabel("width (m, 20 m grid)"); ax.legend(); ax.grid(alpha=.3)
    fig.tight_layout(); OUT.mkdir(exist_ok=True); fig.savefig(OUT / "transect_widths.png", dpi=110)
    with open(OUT / "transects.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    summary = {}
    for rid in sorted({r["roi_id"] for r in rows}):
        rr = [r for r in rows if r["roi_id"] == rid]
        a = np.array([r["low_band_width_2025_m"] for r in rr], float); b = np.array([r["low_band_width_2026_m"] for r in rr], float)
        ok = ~np.isnan(a) & ~np.isnan(b)
        summary[rid] = dict(stations=len(rr), paired_valid=int(ok.sum()),
            stations_with_band_2025=int((a[ok] > 0).sum()), stations_with_band_2026=int((b[ok] > 0).sum()),
            median_width_2025_m=float(np.median(a[ok])), median_width_2026_m=float(np.median(b[ok])),
            stations_wider_by_40m_or_more=int(((b - a)[ok] >= 40).sum()),
            median_contrast_width_2025_m=float(np.nanmedian([r["contrast_band_width_2025_m"] for r in rr])),
            median_contrast_width_2026_m=float(np.nanmedian([r["contrast_band_width_2026_m"] for r in rr])),
            stations_contrast_wider_by_40m_or_more=int(sum((r["contrast_band_width_2026_m"] - r["contrast_band_width_2025_m"]) >= 40 for r in rr)),
            median_min_ndvi_2025=float(np.nanmedian([r["min_ndvi_2025"] for r in rr])),
            median_min_ndvi_2026=float(np.nanmedian([r["min_ndvi_2026"] for r in rr])))
    meta = dict(config=dict(low_ndvi=LOW, contrast_below_profile_median=CONTRAST, centre_window_m=CENTRE_M, half_transect_m=HALF_M, step_m=STEP_M, station_spacing_m=STATION_M, valid_scl=sorted(VALID_SCL)),
                inputs={str(p.relative_to(REPO)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(RUN.glob("*/*.tif")) if p.stem in ("red", "nir", "scl")} | {str(ROIS.relative_to(REPO)): hashlib.sha256(ROIS.read_bytes()).hexdigest()},
                dates=dict(reference="2025-06-15 (S2C_35VLE_20250615_0_L2A)", target="2026-06-20"), summary=summary,
                limitations=["Widths are ground metres along EPSG:3301 transects (10 m steps) sampled from a 20 m EPSG:6933 grid (about 12 m x 33 m ground cells): effective resolution 12-33 m depending on direction", "20 m grid: roads narrower than ~20 m are mixed pixels and may not fall below the NDVI limit",
                             "Centreline is derived from the manual 40 m sampling buffer, not surveyed",
                             "Low NDVI also marks bare soil, harvest, earthworks and cloud-shadow residue; it is not a road label",
                             "Single scenes per year; phenology and moisture differences remain"])
    (OUT / "transect_summary.json").write_text(json.dumps(meta, indent=2))
    print(json.dumps(summary, indent=1))

if __name__ == "__main__":
    main()
