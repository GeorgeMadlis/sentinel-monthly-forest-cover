#!/usr/bin/env python3
"""synthesis-01: write source list, claims, the HTML reference table and the bundle manifest."""
import csv, hashlib, html, json
from pathlib import Path
B = Path(__file__).resolve().parents[1] / "synthesis_report"
SOURCES = [
 ("S01","Maa- ja Ruumiamet","Historical orthophoto WMS (of2023mets, of2024asulad, of2025aero; basic maps pk_vr2024, pk_vr2026)","https://kaart.maaamet.ee/wms/ajalooline","flights 2023-06-09, 2024-05-03, 2025-04-03; retrieved 2026-10-24","Presence/absence before July 2025; road width 2023 vs 2025","geo-01 GS-07..GS-12"),
 ("S02","Maa- ja Ruumiamet Geoportaal","Orthophoto download lists per map sheet (flight dates)","https://geoportaal.maaamet.ee/index.php?lang_id=1&page_id=610","listing retrieved 2026-10-24","True flight dates; no flight after 2025-04-03","geo-01 GS-05, GS-06"),
 ("S03","Maa- ja Ruumiamet","Current orthophoto WMS (EESTIFOTO)","https://kaart.maaamet.ee/wms/fotokaart","current = 2025-04-03 flight; retrieved 2026-10-24","No newer national imagery","geo-01 GS-10"),
 ("S04","Maa- ja Ruumiamet (ETAK) via Keskkonnaagentuur GeoServer","ETAK roads, rail, cutlines, power lines (WFS)","https://gsavalik.envir.ee/geoserver/etak/wfs","state 2026-10-24","No mapped road or rail along the outlines","geo-01 GS-13; works-01 E01-E03"),
 ("S05","Maa- ja Ruumiamet","Rail Baltic county-plan corridor and planning restriction (WFS)","https://gsavalik.envir.ee/geoserver/planeeringud/wfs","plan legal date 2018-02-14","ROI-01 identity","works-01 E04, E05"),
 ("S06","Maa- ja Ruumiamet","Cadastre: 'Rapla-Pärnu raudtee' and '4 Tallinn-Pärnu-Ikla tee' parcels (WFS)","https://gsavalik.envir.ee/geoserver/kataster/wfs","registrations 2020-2026","Land acquisition for Rail Baltica and road 4","works-01 E06-E08"),
 ("S07","Keskkonnaagentuur","Metsaregister forest notices, valid and archived (WFS)","https://gsavalik.envir.ee/geoserver/metsaregister/wfs","approvals 2016-2026","Clearing permits (RD) in both corridors","works-01 E09, E10"),
 ("S08","Transpordiamet","Road register (Teeregister) ArcGIS service: road 4 km points and sections","https://gis.transpordiamet.ee/arcgis/rest/services/Teeregister/MapServer","km points 2026-10-22","Project km positions vs ROI-02","works-01 E21, E22"),
 ("S09","Transpordiamet","Tallinna–Pärnu–Ikla maantee ehitustööd 2026–2027 (project page)","https://transpordiamet.ee/tallinna-parnu-ikla-maantee-ehitustood-2026-2027","updated 2026-06-09","Halinga–Kangru and Are bypass scope and contracts","works-01 E23"),
 ("S10","Transpordiamet","News: Halinga–Kangru 2+2 tender received six bids","https://www.transpordiamet.ee/uudised/tallinna-parnu-ikla-maantee-halinga-kangru-22-teeloigu-ehitushankele-esitati-kuus-pakkumust","2025-09-26","Halinga–Kangru procurement","works-01 E24"),
 ("S11","Transpordiamet","News: Halinga railway viaduct demolition","https://www.transpordiamet.ee/uudised/transpordiamet-koos-kaitsevaega-varistab-halinga-raudteeviadukti","2026-03-25","First dated Halinga–Kangru works","works-01 E25"),
 ("S12","Transpordiamet","News: largest road construction works on the Tallinn–Pärnu road","https://transpordiamet.ee/en/news/largest-road-construction-works-tallinn-parnu-national-road-will-bring-traffic-changes","2026-03-05","Works on road 4 in 2026","works-01 E18"),
 ("S13","ERR","Algavad Are möödasõidu 2+2 teelõigu ehitustööd","https://www.err.ee/1609925537/algavad-are-moodasoidu-2-2-teeloigu-ehitustood","2026-01-29","Are bypass works start 2026-02-02","works-01 E16"),
 ("S14","ERR","Uuel aastal algavad Tallinna-Pärnu maanteel üha suuremad ehitustööd","https://www.err.ee/1609874658/uuel-aastal-algavad-tallinna-parnu-maanteel-uha-suuremad-ehitustood","2025-12-04","Road 4 project overview","works-01 E15"),
 ("S15","ERR","Are möödasõidule tuleb uus ehitushange","https://www.err.ee/1609737930/are-moodasoidule-tuleb-uus-ehitushange","2025-07-04","Are bypass tender re-run","works-01 E17"),
 ("S16","ERR","Transpordiamet ja kaitsevägi varistasid vana Halinga raudteeviadukti","https://www.err.ee/1609984282/transpordiamet-ja-kaitsevagi-varistasid-vana-halinga-raudteeviadukti","2026-04-02","Halinga viaduct demolished","works-01 E26"),
 ("S17","ERR","Rail Baltic Estonia sõlmis suurimad taristuehituse lepingud Eesti ajaloos","https://www.err.ee/1609696695/rail-baltic-estonia-solmis-suurimad-taristuehituse-lepingud-eesti-ajaloos","2025-05-16","Rail Baltica Tootsi–Pärnu contract","works-01 E12"),
 ("S18","ERR","Rail Balticu Eesti põhitrassi võtmelõikude ehitus algab järgmisel aastal","https://www.err.ee/1609720146/rail-balticu-eesti-pohitrassi-votmeloikude-ehitus-algab-jargmisel-aastal","2025-06-12","Rail Baltica works planned from 2026","works-01 E13"),
 ("S19","Copernicus / Element 84 (AWS)","Sentinel-2 L2A COGs, scene S2C_35VLE_20250615 and 2026-06-20 target","https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/35/V/LE/","acquired 2025-06-15 and 2026-06-20","Physical change after July 2025 (own analysis)","runs/aoi-s2-jja-2025-2026-calibrated; audit-01 authenticated"),
 ("S20","synthesis-01 (own analysis)","NDVI cross-profiles and true-colour section pairs","data/transects.csv","2026-10-24","Corridor change 2025 vs 2026; ground-length correction","scripts/transects.py; scripts/section_crops.py"),
 ("S21","audit-01 (round-0002)","Audit of the earlier Sentinel-1/2 run","evidence/audit-01/audit_report.md","2026-10-24","Input authentication; date conflict reported","round-0002/artifacts/audit-01"),
]
CLAIMS = [
 ("SC-01","ROI-01","Q1","not_supported","No road, track or rail ran along ROI-01 before July 2025.","S01;S02;S04;S19;S20","LG-MARU-ORTHO;LG-S2","Orthophoto feature-scale coverage about 2.4 km; rest at 10-20 m"),
 ("SC-02","ROI-01","Q1","supported","A new linear clearing appeared near ROI-01 between 2025-06-15 and 2026-06-20.","S19;S20","LG-S2","Single scenes; 20 m grid; offset up to about 300 m from the outline in the SW half"),
 ("SC-03","ROI-01","Q1/Q3","supported_with_caveat","The new clearing is most probably Rail Baltica corridor clearing (corridor, parcels and RD notices from 2025-07-04 agree).","S05;S06;S07;S17;S18;S20","LG-MARU-ETAK;LG-ERR;LG-S2","No as-built alignment public; identity from geometry and dates"),
 ("SC-04","ROI-01","Q2","not_applicable","Widening does not apply: no road existed on ROI-01 in 2025.","SC-01","n/a",""),
 ("SC-05","ROI-02 north","Q1","supported_with_caveat","Road 4 existed in 2025 80-200 m east of the outline; no road was on the outline itself.","S01;S04;S08","LG-MARU-ORTHO;LG-TRANSP","Outline interpreted as a coarse trace of road 4; operator to confirm"),
 ("SC-06","ROI-02 north","Q2","not_supported","No widening of road 4 before July 2025 (about 10.6 m in 2023, about 10.0 m in 2025-04).","S01","LG-MARU-ORTHO","Threshold estimate on WMS JPEG, ±1.5 m"),
 ("SC-07","ROI-02 north","Q2","supported","Strong signs of artificial widening of road 4 after July 2025: bare corridor of median about 90 m on 2026-06-20; RD notices 2025-12-10..2026-07-17 along the road; Halinga–Kangru 2+2 contract 2025-11-07.","S07;S08;S09;S19;S20","LG-S2;LG-MARU-ETAK;LG-TRANSP","Permit dates are not felling dates; 20 m satellite grid"),
 ("SC-08","ROI-02 middle/south","Q1","not_supported","No road existed on the south part of ROI-02 in 2025 (fields and farmyards).","S01;S19;S20","LG-MARU-ORTHO;LG-S2",""),
 ("SC-09","ROI-02 middle/south","Q1/Q3","supported_with_caveat","The south part is the new road-4 Are bypass (km 108.5-115.8): new parcels from 2025-05-22, RD notices from 2025-12-11, works from 2026-02-02, earthworks and a junction visible on 2026-06-20.","S06;S07;S08;S09;S13;S19;S20","LG-MARU-ETAK;LG-TRANSP;LG-ERR;LG-S2","No public design map; middle part less certain"),
 ("SC-10","ROI-01;ROI-02","Q3","supported","Maa- ja Ruumiamet flight date of the 2025 orthophoto is 2025-04-03; the WMS metainfo value 2023-06-09 is stale; no orthophoto after 2025-04-03 exists.","S02;S03","LG-MARU-ORTHO-META","Date from official file names, not embedded metadata"),
 ("SC-11","ROI-01;ROI-02","geometry","supported","Stored ROI lengths and the 40 m buffer are EPSG:6933 planar values; ground lengths are 18.3 km and 8.6 km.","S20","synthesis-01","Areas in hectares stay correct"),
]
def main():
    d = B / "data"; d.mkdir(exist_ok=True)
    with open(d / "synthesis_sources.csv", "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["source_id","publisher","title_or_layer","url_or_path","date","used_for","agent_record"]); w.writerows(SOURCES)
    with open(d / "synthesis_claims.csv", "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["claim_id","roi_id","question","status","statement","evidence_ids","source_lineage","limitations"]); w.writerows(CLAIMS)
    rows = []
    for sid, pub, title, url, date, use, rec in SOURCES:
        link = f'<a href="{html.escape(url)}">{html.escape(title)}</a>'
        rows.append(f"<tr><td>{sid}</td><td>{html.escape(pub)}: {link}<br><small>Agent record: {html.escape(rec)}</small></td><td>{html.escape(date)}</td><td>{html.escape(use)}</td></tr>")
    page = B / "index.html"; s = page.read_text()
    start, end = "<!-- REFS -->", "<!-- /REFS -->"
    if end in s:
        s = s[: s.index(start)] + start + "\n" + "\n".join(rows) + "\n" + s[s.index(end):]
    else:
        s = s.replace(start, start + "\n" + "\n".join(rows) + "\n" + end)
    page.write_text(s)
    files = sorted(p for p in B.rglob("*") if p.is_file() and p.name != "bundle_manifest.json")
    manifest = {"bundle": "synthesis-01 offline report", "created_utc": "2026-10-24", "files": {str(p.relative_to(B)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
    (B / "bundle_manifest.json").write_text(json.dumps(manifest, indent=1))
    print(len(files), "files")
if __name__ == "__main__":
    main()
