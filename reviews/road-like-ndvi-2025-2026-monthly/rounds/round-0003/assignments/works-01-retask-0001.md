# works-01 retask addendum 0001 (issued by synthesis-01, 2026-10-24)

Base assignment: assignments/works-01.md (unchanged, sha256 dd682c9a...). This addendum narrows the questions and adds operator-authorized online access to public, free sources. No credentials, paid services or bulk downloads.

## Questions
W1. Which official road (number/name), rail line or other infrastructure lies on each ROI centreline? Establish identity by geometry (road register / ETAK / project maps), not by name or proximity alone.
W2. Did that road exist in 2025 (and before)? Give dated evidence (register entry, construction completion, opening date).
W3. Were there construction, reconstruction, widening (e.g. 2+2 lanes), new alignment, embankment or corridor-clearing works on these sections in 2024-2026? Give project names, contract/procurement IDs, dates, chainage (km) and official URLs.

## Candidate sources (verify first)
- Transpordiamet (formerly Maanteeamet / "Teeamet"): road works pages, project pages, press releases, Teeregister (road register) map, traffic restrictions / tarktee.ee.
- Rail Baltic Estonia (rbestonia.ee) design/construction sections and maps for Pärnu county.
- Riigihangete register (riigihanked.riik.ee) for contract IDs.
- Maa- ja Ruumiamet / planeeringud, local government (Põhja-Pärnumaa, Tori, Pärnu linn) planning documents.
- Use original Estonian search terms (e.g. "teelõigu ehitus", "2+2", "laiendamine", "rekonstrueerimine", "Rail Baltica Pärnumaa põhitrassi ehitus", place names near the coordinates).

ROI geometry (WGS84 lon,lat; simplified outline of a 40 m buffer around a manual coarse centreline; full vertices in inputs/prior_rois.geojson):
- ROI-01, about 22.5 km, SW->NE: (24.5962,58.4266) -> (24.6410,58.4629) -> (24.6928,58.4891) -> (24.7570,58.5137) -> (24.8146,58.5426). EPSG:3301 bounds approx X 534831-547437, Y 6476401-6489452.
- ROI-02, about 6.4 km, N->S: (24.5093,58.5853) -> (24.5111,58.5669) -> (24.5322,58.5502) -> (24.5421,58.5270) -> (24.5394,58.5119). EPSG:3301 bounds approx X 529681-531555, Y 6485856-6494055.
- CONTROL-01 around (24.6857,58.5777); CONTROL-02 around (24.8071,58.3178) (stable-looking forest, no stability label).
Periods of interest: before July 2025 (pre) and after July 2025 (post); calendar years 2024, 2025, 2026.

## Outputs (write only in artifacts/works-01/)
works_ledger.csv, works_claims.csv, works_primary_evidence.json (per assignment), plus images/ with official project maps or figures only where the licence allows local copies (otherwise link), and README.md summarising positive and negative findings. Record every URL, document date, event date, retrieval UTC time, SHA-256 of saved files and geometry-match confidence. Do not use Sentinel/EO conclusions.

Budget: at most 120 tool calls / 60 minutes.
