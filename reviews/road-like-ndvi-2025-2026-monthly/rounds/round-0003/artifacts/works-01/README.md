# works-01: official infrastructure records for ROI-01 and ROI-02 (round-0002, retask 0001)

Role: `official-infrastructure-records`. Host: Claude Code, a subagent spawned by synthesis-01.
Executed 2026-10-24 between 16:37 and about 16:52 UTC. This work is independent of any Sentinel/EO conclusion. No files under
`reviews/20261006T174722Z-sentinel-road-investigation` or `artifacts/audit-01` were read.

All geometry checks intersect official vectors with `inputs/prior_rois.geojson`. The vectors come from
the Maa- ja Ruumiamet / Keskkonnaagentuur public WFS at `gsavalik.envir.ee`: ETAK, cadastre, planning corridor, EHAK and Metsaregister.
Computations use EPSG:3301. Chainage values ("km") refer to the 5-vertex simplified centrelines in the retask addendum.
They are not road or rail chainage. See `works_ledger.csv` for sources, `works_claims.csv` for claims and
`works_primary_evidence.json` for file hashes. Maps are in `images/map_roi01.png` and `images/map_roi02.png`.
They are derived figures from the open data listed in the ledger.

Stage vocabulary: *plan* / *land acquisition* / *permit (clearing notice)* / *contract* / *work started* /
*work completed* / *feature existed*. These are kept separate. A registry entry or notice approval does not prove felling.

## ROI-01 (about 22.5 km, SW→NE, Tori vald: Kilksama → Rütavere → Võlla → Suigu → Kuiaru → Selja → Murru → Muti)

- **W1 identity.** ETAK has no road or rail along ROI-01. The ROI only crosses local tracks, and a 143 m piece of broad-gauge
  rail at the NE end. The **NE part (simplified chainage ~10.5–17.3 km) lies inside the 2018 county-plan Rail Baltic
  railway corridor**, which accounts for 46.0 % of the ROI area. The plan is "Rail Baltic raudtee trassi koridori asukoha määramine", legal date 2018‑02‑14.
  It also intersects state cadastral units named **"Rapla-Pärnu raudtee NNN"** (Rail Baltica land). These cover 12.8 % of the ROI
  area, rising to 12–87 % per 500 m bin at 12–17 km. Most of these units were registered in 2025.
  Geometry-match confidence for the NE part: **high for the RB corridor and land, but not for an as-built alignment.**
- **SW part (0–~10 km): identity indeterminate.** This part runs parallel to the RB corridor but 6–330 m outside it,
  through state forest ("Taali metskond"). It has no RB parcels and no raadamine notices at 0–5 km. A coarse-centreline offset from RB is
  plausible but not shown. Do not attribute it to Rail Baltica on proximity.
- **W2 existence.** No infrastructure existed on the ROI before 2025 according to official records. The planning corridor existed from 2018.
  Pre-2024 records show only routine clear-cut notices (2017–2023) and small raadamine notices in 2018–2020 and 2023‑03‑21.
- **W3 works.** 37 Metsaregister **raadamine (RD) notices approved 2025‑07‑04 … 2026‑09‑07** overlap
  ROI-01. They cover 26.7 ha of overlap, 14.8 % of the ROI. 21 of them were approved on 2025‑09‑11 or 2025‑09‑24, and most sit on "Rapla-Pärnu raudtee"
  parcels at 11–17 km. The ROI lies on the **Rail Baltica Tootsi–Pärnu section**. Its alliance design-and-build contract
  (Tootsi–Pärnu substructure plus Ülemiste–Pärnu superstructure, about 394 MEUR) was signed **2025‑05‑16**, followed by about 1 year of
  development, with active works planned for 2026–2030 (ERR, 2025‑05‑16 and 2025‑06‑12). The two ERR articles disagree on the lead partner (GRK vs Bouygues).
  The adjacent Selja–Tootsi section (Tariston, 16 km) is NE of Tootsi, outside ROI-01.
  **Whether felling or earthworks actually happened in 2025 or 2026 is not established by any official record found.**

## ROI-02 (about 6.4 km, N→S: Tarva, Kangru (Põhja-Pärnumaa) → Parisselja, Elbu, Kurena (Tori vald))

- **W1 identity.** The existing **road 4 Tallinna–Pärnu–Ikla is not on ROI-02**: 0 m of it lies inside the ROI.
  The ROI runs 80–200 m west of road 4 in the north and diverges by up to about 2.9 km in the south. No other road or rail is along it.
  The **southern part (~6.5–8.6 km) coincides with new "4 Tallinn-Pärnu-Ikla tee" transport-land parcels registered
  2025‑05‑22 and later** in Elbu and Parisselja. These cover 12.1 % of the ROI area, rising to 18–85 % per bin. RD notices fall in the same stretch.
  This matches the described extent of **road 4 "Are möödasõit" 2+2, km 108.5–115.8, "largely on a new alignment" starting
  at the Kangru/Parisselja village boundary**. Confidence is medium for the southern part. No design map was found.
- **Northern part (Tarva/Kangru, 0–~4.5 km): identity indeterminate.** It lies north of the stated bypass start. The
  Halinga–Kangru 2+2 project (km 103.5–108.5) is described as staying on the existing alignment, so it does not explain a
  corridor offset 80–200 m to the west.
- **W2 existence.** The ROI-02 corridor was not a registered road in 2025. Road 4 nearby has existed for a long time (ETAK geometry since 2008).
  There were no RD clearing notices in the ROI before 2025‑12.
- **W3 works.** 7 RD notices approved **2025‑12‑11 … 2026‑07‑17** overlap ROI-02, covering 5.4 ha (10.4 %).
  One example is 50001183094 on parcel 80901:001:1665 "4 Tallinn-Pärnu-Ikla tee": 816 m long, 83 % inside the ROI.
  The contract is with **AS TREF Nord, 36.46 MEUR + VAT, 30 months, 85 % EU co-financed**. Per ERR (2026‑01‑29), construction
  started on **2026‑02‑02, with clearing first** and earthworks from March 2026. The tender was re-run after a VAKO decision (ERR 2025‑07‑04).

## Negative findings and blockers

- No Rail Baltica or new road-4 alignment in ETAK. No pipelines. Power lines and cutlines only cross the ROIs.
- `yld_plan_transp` has no features in either bbox. No design geometry for the Are bypass or the RB alignment exists in the public planning WFS.
- riigihanked.riik.ee is a JS application and its API returned HTTP 500, so **no procurement IDs** were obtained. The
  Transpordiamet contract no. 3.2‑3/25/1687‑1 appears only in a search snippet and is unverified.
- railbaltica.org `?p=54799` returned 404 and `info.railbaltica.org` did not resolve, so no RB permit or works log was retrieved.
- A Transpordiamet permit PDF returned by search was for road 9 (Herjava), so it is unrelated (E19).
- The control polygons are outside the download bboxes and were **not assessed**.

## Limitations

- News articles (ERR) are secondary sources and form one lineage. Notice approval dates are not felling dates. Cadastral
  registration is land acquisition, not construction.
- Metsaregister work-code meanings (RD = raadamine, LR = lageraie, HR = harvennusraie, SR = sanitaarraie) are standard
  but were not re-verified against a code list in this round.
- Downloads under `downloads/` total about 12 MB. They include copyrighted ERR HTML snapshots kept only for hashing. Consider
  excluding them from git and redistribution.
- These are disturbance-screening candidates. Nothing here establishes legal deforestation, confirmed forest state or cause.

## Retask 0002 (W4–W6: road 4 Halinga–Kangru and project km vs ROI-02 latitudes)

Retask 0002 was executed 2026-10-24 between 16:52 and about 17:00 UTC. The addendum is `round-0003/assignments/works-01-retask-0002.md` (sha256 678feb94…).
New sources are E21–E27 and N05. New claims are C16–C21.

**W4 — Halinga–Kangru 2+2, km 103.5–108.5 (Transpordiamet project page, last updated 09.06.2026).**
- Contract with KMG OÜ + Infragreen OÜ, **signed 7.11.2025**: 25.5 MEUR + VAT, 85 % EU-funded.
- Start planned for H1 2026, with 30 months of construction (the page also labels it "ehitusaeg 2026–2027"). The planned end is therefore about 2028. No completion is documented.
- Route: "kopeerib asukoha mõttes olemasolevat trassi". The section runs from 0.5 km Tallinn-side of the old railway viaduct to the Kangru/Parisselja village boundary. This is **widening on the existing alignment, not a new route**.
- Scope: a low-clearance tunnel, a grade-separated local junction, a main-road bridge and an ecoduct.
- First dated physical work found: the **old Halinga railway viaduct was demolished on 2026-04-02** (ERR; Transpordiamet notice 25.03.2026).
- Roadside raadamine notices along road 4 were approved from 2025-12-10 to 2026-07-17, most of them on 2026-01-12.
- Neighbouring contracts:
  - Libatse–Halinga (km 98.4–103.5): AS TREF Nord, signed 27.02.2026.
  - Are möödasõit (km 108.5–115.8, 6.9 km): AS TREF Nord, signed **18.11.2025**, 36.5 MEUR. Works started 2026-02-02 according to ERR.

**W5 — km positions.** These come from Teeregister km points (gis.transpordiamet.ee, created 2026-10-22), interpolated linearly between points.
- km 103.5 is at 58.5877 N, 24.5123 E.
- km 108.5 is at 58.5467 N, 24.5382 E. The Kangru/Parisselja boundary crosses road 4 at 58.5478 N, about 130 m away, which is consistent.
- km 115.8 on the old road is at 58.4875 N, 24.5290 E. The bypass end on the new alignment is not mapped.
- **North stretch (58.550–58.585):** within the Halinga–Kangru km range (about km 103.8–108.0). The ROI lies **82–203 m (median 177 m) west of the registered carriageway**, and 0 m of road 4 is inside it. The ROI is therefore *not* on the widened road within the 40 m tolerance, and its identity remains unresolved.
- **Middle stretch (58.528–58.550):** from 58.550 to about 58.547 it is the last part of Halinga–Kangru. South of that it falls in the Are möödasõit range, where the ROI departs from the old road (82 → 810 m), consistent with the bypass new alignment.
- **South stretch (58.513–58.528):** Are möödasõit, 660–830 m from the old road. It coincides with road-4 parcels registered in 2025–26 and with RD notices. The bypass continues south of the ROI end.

**W6 — within ±200 m of the north stretch.**
- **18 RD notices**: 2025-12-10, 2026-01-12 (×14), 2026-02-10, 2026-03-24 and 2026-07-17. Together they cover 6.2 ha within the zone, and almost all lie 11–19 m from the carriageway (roadside clearing for widening).
  - Only two overlap the ROI band: 50001189087 (2026-01-12, 3 786 m², 58.5617 N) and 50001226380 (2026-07-17, 319 m², 58.5505 N). Together they cover 1.4 % of the band area.
- **25 road-4 parcels registered 2025-08-25 to 2026-10-22** lie along the existing road. Only three touch the ROI band, covering ≤ 820 m² each.
- Road-4 parcels registered 2022-08-16 overlap the ROI near 58.563 N (8 303 m²).
- There are no RD notices in the zone before 2025.
- Summary: the official clearing and land-acquisition footprint follows the existing road, not the ROI-02 north stretch.

Limitations:
- Linear km interpolation is accurate to about ±50 m.
- Carriageway 2 in the register is a placeholder that coincides with carriageway 1.
- No design drawings were obtained for either project.
- riigihanked IDs are still missing.
