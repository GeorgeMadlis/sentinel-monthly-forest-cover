---
name: research-sentinel-change
description: Search and critically assess journal publications and technical reports about Sentinel optical/SAR change, road detection, thresholds and the confounders of a specific observed linear feature.
---

# Research the interpretation and methods

Read [investigation contract](references/investigation-contract.md). Read prior visual findings and each ROI claim. Investigate mechanisms rather than searching only for confirmation.

1. Search current scholarly/official sources for: Sentinel-2 NDVI and road construction/linear clearing; narrow-feature detectability/mixed pixels; Sentinel-1 RTC VV/VH changes and road orientation, moisture and surface scattering; optical/SAR AND vs probabilistic fusion; registration/cloud/calibration artifacts; robust change thresholds and temporal persistence. Include geographic/land-cover terms derived from AOI, not assumed country.
2. Prefer peer-reviewed original studies, author-hosted manuscripts and provider technical reports. Read methods/results and relevant pages, not just search snippets. Distinguish full text, abstract only, and inaccessible. Verify author/year/title/DOI. Record search query, date, inclusion/exclusion reasons and unsuccessful searches. Aim for 6–10 directly relevant sources; report honestly if fewer exist.
3. For each source extract sensor/product, spatial resolution, geography/cover, baseline/target sampling, preprocessing, algorithm, labels/validation, errors, limitations and transferability to this run. Separate empirical findings from your inference. Literature that demonstrates road detection somewhere does not confirm this ROI. Do not transfer a threshold without checking units, direction, sample size and calibration.
4. Start time-series review with Verbesselt et al. 2010 BFAST (doi:10.1016/j.rse.2009.08.014) and Zhu & Woodcock 2014 CCDC (doi:10.1016/j.rse.2014.01.011). Verify originals. These are time-series frameworks, not validated replacements for this short baseline. Search for direct Sentinel/road evidence as well; do not present these seeds as such evidence.
5. Assess the proposed MAD/effect-size/persistence experiments and distinguish heuristic screening from calibrated error control. Explain why missing SAR, an AND rejection or sigma score cannot settle road existence. Recommend only methods whose data requirements can be met; list unavailable longer-series methods separately.
6. Write research/literature_review.md, research/references.bib and research/literature_evidence.json. Cite URLs/DOIs and page/section for each material assertion; keep quotes short. Update investigation.json with source IDs, evidence-to-claim relationships, uncertainties and implementable recommendations. Run the review site builder from the contract. Never claim this stage confirms the road.
