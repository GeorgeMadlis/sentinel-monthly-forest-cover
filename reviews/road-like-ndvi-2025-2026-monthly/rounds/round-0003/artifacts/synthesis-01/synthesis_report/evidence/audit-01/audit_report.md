# audit-01: authenticated local-cache audit

Audit scope completed; scientific conclusions and output acceptance remain for human review. The round-0002 graph and this step alone were authorized. No remote access, downloads, paid external service, native subagent, later scientific role, baseline ingestion, public release or knowledge promotion occurred. Exact serving-model/client/billing details are not exposed; existing-session model billing is not claimed free.

## Geometry and user directions

The user confirms that the two outlined corridors are the intended targets. Their polygon coordinates and both controls are preserved byte-for-byte (SHA-256 b079d3dbff8a473daf6e3d33cdfdaedffc29de470425b8fe9a212f796a862125). All four geometries are valid and inside the AOI. Raw reference/target and outline figures were inspected, as were all four existing decision variants and both controls. The outlines follow the intended coarse corridors; they are sampling buffers, not surveyed road edges. No coordinates were moved or centreline invented. Control stability is not independently labeled.

The prior '*-native.png' files are explicitly generated from 20 m analytical crops in finish_review.py; filenames do not establish native 10 m evidence. All current audit crops are labeled 20 m. Multiple subpixel/road-edge claims remain outside this QA.

## Historical hash mismatch resolution

The calibrated optical manifest passes 59/59 output hashes. The sigma/radar manifest passes 213/226; the same 13 known derived/presentation mismatches persist. All 301 entries in the historical originals-before ledger and all 910 historical artifact-manifest entries still match. All 1,514 original run/review files match this audit's before/after fingerprints.

Resolution: preserve every original manifest and byte, exclude mismatching derivatives as evidence of the original manifest version, authenticate the 79 consumed local source assets against original output hashes, and regenerate the decisions in this audit with new checksums. This establishes a usable reproduced evidence chain without pretending the missing original expected bytes were recovered. Three current display masks also equal the reconstructed decisions on every pixel, despite two display-mask files differing in file hash; file-byte mismatch alone therefore does not imply a changed candidate array.

Historical provenance fails against today's graph because historical pins differ; each manifest PASSES against its own historical graph recovered from local Git (no fetch or checkout). The separate new audit run_manifest.json passes the current Lab run schema and semantic-provenance validator, with actual current pins and script/output checksums. None of these checks establishes scientific validity.

## Formulas, dates and calibration

NDVI=(NIR-Red)/(NIR+Red), calculated per SCL-screened observation. Archived change is **absolute current minus reference NDVI**, not relative percentage. Fixed optical: delta < -0.2 against the selected 15 June 2025 scene. Sigma optical: 20 June 2026 NDVI minus mean of eight selected summer-2025 dates < -2 population SD, with at least two valid references and positive SD. A single reference RGB scene does not depict that eight-date mean.

Reference dates are 14/15/30 June, 4/25 July and 4/14/26 August 2025. The selected full-AOI optical target is 20 June 2026. These are not full calendar-June means. The selected full-AOI inventory has only one June-2026 optical target; additional historical persistence crops are small windows, not full-corridor month support. This audit did not create monthly pairs.

Harmonized source reflectance uses scale .0001 with offset zero after the recorded BOA offset application; cached reflectance uses scale 1/offset 0. No second -0.1 offset was applied. Selected reference/target processing baselines are 05.11/05.12. SCL valid classes are 4,5,6,7; no dilation. Continuous source materialization uses bilinear resampling, SCL uses nearest; the audit rereads exact aligned 20 m caches. Missing evidence remains nodata.

Radar: ascending relative orbit 160, twelve selected acquisitions per summer, linear intensity transformed by 10log10 then temporal median in dB for both years. Candidates require deltaVV < -1.5 AND deltaVH < -1.0 dB. Combined masks are paired-valid AND, not calibrated probabilities or independent causal confirmation.

| Reproduced mask | Candidate pixels | Disagreeing values / validity |
|---|---:|---:|
| Fixed optical | 91,291 | 0 / 0 |
| Sigma optical | 121,242 | 0 / 0 |
| Radar | 119,603 | 0 / 0 |
| Sigma AND radar | 12,875 | 0 / 0 |

Fixed AND radar also reproduces 9,469 pixels in the current comparison mask. All eleven continuous raster/count comparisons pass 2e-6 tolerance, with maximum observed error 2.384185791015625e-7 and zero validity disagreements. These are audit reproducibility counts, not new forest-loss estimates.

## Registration and orthophoto cutoff

The two repeated 40x40 optical landmark tests both prefer [0,0] integer shift, with correlations 0.9420274456542702 and 0.7856362709960444. No shift was applied. This does not certify subpixel, full-corridor or SAR alignment.

The requested orthophoto rule is recorded: verified before-July-2025 images vs verified after-July-2025 images, and pre-cutoff only if no post-cutoff photo is available. The precise July boundary is not yet frozen; see orthophoto_boundary_note.json. No image is assigned under either boundary interpretation. The available cached 2025 layers conflict with generic 2023-06-09 metadata; neither is an authenticated acquisition date for the returned pixels. Other cached 2023/2024 windows lack usable imagery. No verified post-cutoff image is established in this cache, and availability elsewhere was not checked. Keep available imagery as undated physical context; relaxing the window does not resolve flight-to-image linkage. No construction interval follows.

## Hansen and later technical work

Hansen 2024 product selection is recorded as DS-0001, v1.12. No Hansen/treecover/lossyear mask was found in the checked Sentinel runs/data/configs directories, and none was downloaded. The Lab v1 contract uses treecover2000 and explicitly labels year-2000 baseline extent. It is not measured 2024 canopy cover. A remaining-cover proxy using annual loss needs an explicit reviewed temporal transformation and does not account for all regrowth. That contract decision stays outside this audit; no forest-specific estimates were made.

The archived sigma sample already selects unique optical calendar dates; generic monthly item counting still needs overlap/reprocessing protection. Choose explicit acquisition grouping and overlap/mosaic QA, preserve per-pixel membership, and test duplicate items before later monthly execution. Mask-dilation sensitivity needs a separate declared preprocessing parameter. A future deterministic reconciler should join claim/ROI/period with exact source hashes, retain conflicting statuses and shared lineage, and never vote an agent consensus into truth. A reviewed-evidence release adapter must verify all output links/hashes/licenses and human gates. These implementation choices are proposals, not execution of later graph nodes.

The current round's executed assignment remains unchanged. Any revised later-role harness or year-2024 temporal assumptions belong in a successor plan/round; no approval is inherited by discovery, quantification, corroboration, challenge or release.

## Evidence navigation

- [Source authentication](cache_authentication.json)
- [Exact reproduction](reproduction.json)
- [Geometry QA](geometry_qa.json) and [unchanged ROIs/controls](roi_review.geojson)
- [Offline per-ROI comparison](inspect/comparison.html)
- [Mask contact sheet](inspect/mask_contact_sheet.png)
- [Source dates and URLs](source_dates.json)
- [New audit run manifest](run_manifest.json)
- [Historical provenance checks](historical_provenance_checks.json)
- [Orthophoto date audit](orthophoto_date_audit.json)
- [Hansen contract/availability audit](forest_baseline_audit.json)

Disturbance candidates are not legal deforestation, confirmed forest state or causal loss labels. Hansen annual loss is not monthly ground truth. Sensor agreement does not establish cause.
