# Sentinel linear-feature review

A newly constructed road is not established. The two sampled candidates show optical linear-change patterns, but their interpretation remains conditional. ROI-02’s sampled main road was already visible in the 15 June 2025 reference; new branches, widening or surrounding clearing are separate unresolved claims. ROI-01 retains forestry-track, railway/earthworks and road hypotheses. No prior-forest or legal-deforestation conclusion is justified.

| Claim | ROI-01 | ROI-02 |
| --- | --- | --- |
| linear_change | supported | supported |
| road_identity | unresolved | unresolved |
| new_construction | unresolved | rejected |
| appearance_interval | unresolved | unresolved |
| prior_forest | not_tested | not_tested |
| legal_attribution | not_tested | not_tested |

## Sensor evidence and denominators

Run: aoi-s2-s1-jja-2025-2026-sigma; AOI: example-aoi in Estonia. Purpose: v2-style provisional disturbance screening plus an adjacent linear-feature review, not validated monthly forest monitoring. Area: determinant of 20 m EPSG:6933 equal-area grid, 0.04 hectares/pixel. No forest gate. These are all-land-cover candidate hectares.

| Variant | Candidates | Hectares | Valid pixels |
| --- | --- | --- | --- |
| fixed | 91291 | 3651.64 | 3255306 |
| fixed_sar | 9469 | 378.76 | 3255306 |
| sigma | 121242 | 4849.68 | 3255351 |
| sigma_sar | 12875 | 515.0 | 3255351 |

| Pair | Both positive | Optical-only | Radar-only | Neither | Joint valid | Unavailable grid pixels |
| --- | --- | --- | --- | --- | --- | --- |
| fixed | 9469 | 81822 | 110124 | 3053891 | 3255306 | 4657 |
| sigma | 12875 | 108367 | 106719 | 3027390 | 3255351 | 4612 |

Fixed and sigma must each be compared with their own SAR variant. The fixed optical reference is one 15 June 2025 acquisition; sigma uses a mean/std of eight selected 2025 summer dates. Target optical is 20 June 2026. Radar is twelve selected dates per summer, ascending orbit 160, linear power converted to dB before median composition. The strict radar gate is ΔVV < −1.5 dB AND ΔVH < −1 dB. The combined mask is paired-valid optical AND radar; zero optical-valid/radar-unavailable pixels explains that all removed optical candidates fail thresholds. Missing pixels are never filled with zero. Narrower masks do not demonstrate greater accuracy or physical road absence.

Fixed retains 9,469/91,291 optical candidates (10.37%); sigma retains 12,875/121,242 (10.62%). The displayed reference RGB is not the eight-date sigma/robust composite. Calibration uses archived gain=.0001 and no second BOA offset for flagged COGs; the provider interpretation is documented, not independently radiometrically validated. SCL 4/5/6/7 is accepted, with nearest quality and bilinear continuous resampling. No spatial SAR speckle filter is applied; temporal median is declared. Summer SAR and June optical cannot establish the same event date.

## Candidate-region signals

ROIs are provisional manually traced sampling corridors with 40 m buffers, plus two visually stable forest controls. They are not surveyed road footprints. Projected centreline length and rough apparent widths are recorded in rois.geojson. Width approximately 20–60 m is a visual estimate (1–3 analysis pixels); source-pixel equivalents do not constitute native-resolution measurement. Alignment checks at two optical patches preferred zero integer shift (correlations .942 and .786); no correction was made. This does not certify SAR or subpixel registration.

| Region | Joint-valid pixels | Sigma | Sigma+SAR | VV-only failure | VH-only failure | Both failures | Median ΔVV dB | Median ΔVH dB |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ROI-01 | 4511 | 965 | 235 | 395 | 4 | 331 | -0.175 | -0.38 |
| ROI-02 | 1287 | 288 | 93 | 138 | 0 | 57 | 0.304 | -0.087 |
| CONTROL-01 | 256 | 0 | 0 | 0 | 0 | 0 | -0.136 | -0.075 |
| CONTROL-02 | 256 | 0 | 0 | 0 | 0 | 0 | -0.193 | -0.149 |

In ROI-01, 730 sigma candidates fail SAR: 395 fail VV alone, four VH alone and 331 both. In ROI-02, 195 fail: 138 VV alone and 57 both. These are sampled buffers, not full-feature completeness estimates. ROI-level continuous percentiles and rejected-pixel distributions are in roi_metrics.csv and common_support_and_roi_robust.json. Surrounding vegetation and manual-trace uncertainty dilute corridor statistics. Two visual controls have zero optical candidates but a few radar candidates, demonstrating disagreement without proving any accuracy rate.

Possible mechanisms include mixed pixels, moisture/roughness maintaining backscatter, temporal median dilution, seasonal agriculture/phenology, clouds/SCL edges, surface works and registration errors. Literature supports these as alternatives; local cause was not measured. Official Rail Baltic reports describe regional rail and access-road works, but no exact geospatial association was proved. See literature_review.md and corroboration.md.

## Executed threshold and persistence experiments

The supplied robust helper passed five synthetic checks (missing samples, minimum count, zero MAD/noise floor, strict boundaries, shape mismatch). Tile-level calibrated reference mean/std reproduced the archived rasters within 2e−6 on finite support. The experiment uses median m, MAD, score z=(m−target)/max(1.4826 MAD, epsilon); candidates require at least five clear unique reference dates, z>k and m−target>delta_min. Invalid NDVI and missing targets remain unavailable. k={2,2.5,3}, delta_min={.1,.15,.2}, epsilon={.02,.05}: all 18 settings retained, four masks each (optical, AND, OR, discordance), three portable maps each.

Default (2.5,.15,.02): 61,610 optical candidates (2,464.40 ha), 7,582 AND (303.28 ha), 150,257 OR (6,010.28 ha), on 2,735,752 paired-valid pixels. Across all settings optical counts range 45,860–89,317 and AND 5,865–10,217. The default intersection with fixed/sigma support has 2,735,727 valid pixels: fixed=77,092, fixed+SAR=7,812, sigma=92,146, sigma+SAR=9,312, robust=61,610, robust+SAR=7,582. Compare on that intersection rather than treating area differences caused by missing references as improvement.

Three-date persistence was executed in two 500 m windows using 7, 20 and 30 June 2026, at least ten-day separation, AOI-clear ranking and pixel SCL masking. ROI-01: 145 pixels valid on all dates, two recurring detections; ROI-02: 676 valid, 149 recurring detections. Counts/masks and access/calibration evidence are preserved under experiments/persistence/ and cache/persistence/. These are repeated optical anomalies, not independent observations of road identity, full-corridor persistence, the Lab’s consecutive-month confirmation or BFAST/CCDC. No held-out labels, probabilistic fusion, accuracy statistics or calibrated probabilities are claimed.

## Independent imagery and dating

Official historical WMS capabilities and small windows were downloaded. Requested sampling is .5 m; native source resolution remains unverified. 2023/2024 responses contained attribution but no imagery. The 2025 layer shows a paved road and vehicles at ROI-02, and forest clearings/tracks at ROI-01. Generic metainfo says flight 9 June 2023/GSD25 despite the 2025 layer: this contradiction remains unresolved. Neither date is silently assigned to the pixels. Source sheet listing attempts through the web tool failed. No adequately dated independent before/after pair or verified 2026 high-resolution after image was obtained. Appearance interval, widening/reopening and construction identity therefore remain unresolved. The photographs are not a legal forest definition; no baseline or permit evidence was supplied.

## Provenance, tests and review candidates

Graph and downstream-descriptor checks passed without writing: 68 concepts, 72 validated and 67 candidate relations; revision ef90b703ae150c09cc7cac6fd324d7b5ecd8305a5a0d5130ec0deb61ed291e49. Run semantic-provenance validation passed. Full revisions/worktree states, concept versions/status, relationships and contextual corpus hashes are in semantic_trace.json. New experiment helper/code hashes and package versions are in skill_installation.json, artifact_manifest.json and environment.json. No linked concept was past its review-after deadline on 6 October 2026. Validated contract transcriptions/API capabilities do not empirically validate threshold choices; the NDVI method and workflow registrations remain candidates. This is the Lab’s OKF-oriented profile, not asserted full-standard conformance.

13 current run files mismatch the original manifest’s output hashes (manifest_verification.json). The presentation update does not provide replacement hashes for all of them. This was pre-existing: every original/source-run file matched this review’s before/after checksums. Current hashes are pinned, and baseline counts/AND logic independently reproduced. The discrepancy remains a reproducibility limitation; originals were not repaired.

Repository SHA: 28d079efc7c51b510f7e1d7fe196552df2d3c09d; Lab SHA: f3895e46fe3a5109e8bf0e3e01328e942b1e98c5.

Source-grounded candidates are in knowledge_candidates/index.json with schema-checked Markdown records. Proposed IDs are unregistered; all relations remain candidate. Human review, evidence, tests and drift review are required before any canonical promotion. No corpus/generated graph was edited.

The four installed skills and SHA-256 checks are recorded in skill_installation.json. All 36 repository tests passed (repository_tests.log); self-test, graph/descriptor/provenance checks, mask counts, same-grid assertions, original integrity and HTML link checks are archived. Browser rendering was unavailable; raw/derived PNG figures and all threshold overview variants were inspected with image tools.

Reproduction from repository root:

```
.venv/bin/python reviews/20261006T174722Z-sentinel-road-investigation/audit.py
.venv/bin/python reviews/20261006T174722Z-sentinel-road-investigation/experiment.py
.venv/bin/python reviews/20261006T174722Z-sentinel-road-investigation/persistence.py
.venv/bin/python reviews/20261006T174722Z-sentinel-road-investigation/verify_and_figures.py
.venv/bin/python reviews/20261006T174722Z-sentinel-road-investigation/add_metrics.py
.venv/bin/python reviews/20261006T174722Z-sentinel-road-investigation/finish_review.py
```

Run fetch_orthophotos.py only to refresh external queries; response identity may change. Raster experiments reuse cached/calibrated provider windows, tiled IO, pure repository feature/fusion and reporting functions. All review/cache/artifact paths are recorded in investigation.json and artifact_manifest.json. No Earth Engine dependency or canonical update is needed. No generated large raster was committed.

Remaining evidence needed: user-confirmed precise feature or surveyed centreline; independently dated native-resolution before/after imagery; road versus rail/track alignment and construction records; a separately approved prior-forest baseline; and any relevant legal documents. Additional methods requiring multi-year seasonal series or independent holdouts remain proposals.

Hansen annual loss is not monthly ground truth. Monthly outputs in this report are derived from Sentinel composites and (where applicable) trained under annual weak supervision. They have not been validated as month-resolved truth.

Complete original data-source, forest-definition, area-method, limitations and semantic-provenance blocks: original_contract_blocks.json. Literature links and access levels: literature_review.md / references.bib.
