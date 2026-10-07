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


Questions for corroboration: precise road/rail identity, dated independent before/after, reopening/widening, prior forest and legal evidence.
