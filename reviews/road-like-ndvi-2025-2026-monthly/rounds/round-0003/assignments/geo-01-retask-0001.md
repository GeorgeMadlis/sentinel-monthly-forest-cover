# geo-01 retask addendum 0001 (issued by synthesis-01, 2026-10-24)

Base assignment: assignments/geo-01.md (unchanged, sha256 f756bc49...). This addendum narrows the questions and adds operator-authorized online access to public, free sources. No credentials, paid services or bulk downloads.

## Questions
G1. For each dated source, is a road, track, rail or cleared corridor present, absent (with usable coverage), indeterminate or unavailable along ROI-01 and ROI-02 in 2024, 2025 and 2026?
G2. Do dated sources show a change in width of the corridor or carriageway (e.g. new lanes, wider clearing, new embankment) between pre- and post-July-2025 images?
G3. Resolve, if possible, the actual flight/acquisition date of the Maa- ja Ruumiamet orthophoto pixels per map sheet (the WMS "metainfo" layer returned a generic 2023-06-09 date for the 2025 layer).

## Candidate sources (verify endpoints first)
- Maa- ja Ruumiamet WMS: https://kaart.maaamet.ee/wms/ajalooline (historical yearly orthophotos, e.g. of2024aero, of2025aero), https://kaart.maaamet.ee/wms/fotokaart (current orthophoto), alus/ETAK layers; GetCapabilities first.
- Orthophoto metadata / flight dates: Maa-amet Fotoladu, ortofoto sheet index, metainfo layers, geoportaal pages.
- ETAK road/rail vectors (WFS or downloads) and their edition dates.
- Any other official free source (e.g. Estonian Road Register map) that is spatially matched.

ROI geometry (WGS84 lon,lat; simplified outline of a 40 m buffer around a manual coarse centreline; full vertices in inputs/prior_rois.geojson):
- ROI-01, about 22.5 km, SW->NE: (24.5962,58.4266) -> (24.6410,58.4629) -> (24.6928,58.4891) -> (24.7570,58.5137) -> (24.8146,58.5426). EPSG:3301 bounds approx X 534831-547437, Y 6476401-6489452.
- ROI-02, about 6.4 km, N->S: (24.5093,58.5853) -> (24.5111,58.5669) -> (24.5322,58.5502) -> (24.5421,58.5270) -> (24.5394,58.5119). EPSG:3301 bounds approx X 529681-531555, Y 6485856-6494055.
- CONTROL-01 around (24.6857,58.5777); CONTROL-02 around (24.8071,58.3178) (stable-looking forest, no stability label).
Periods of interest: before July 2025 (pre) and after July 2025 (post); calendar years 2024, 2025, 2026.

## Outputs (write only in artifacts/geo-01/)
geo_sources.csv, geo_claims.csv, geo_primary_evidence.json (per assignment), plus images/ with small PNG windows (<=1500 px, a few per ROI section, both years where available, with file names that state ROI, layer and date) and README.md summarising findings, negative results and limitations. Record every URL, request parameters, retrieval UTC time, SHA-256 and license/attribution. Do not use Sentinel/EO conclusions.

Budget: at most 120 tool calls / 60 minutes.
