---
id: method:robust-ndvi-screening
type: method
title: Experimental robust NDVI screening
version: '0.1'
status: candidate
updated: '2026-10-06'
review_after: '2027-04-06'
sources:
- https://doi.org/10.1080/01621459.1993.10476408
- https://gerslab.cahnr.uconn.edu/wp-content/uploads/sites/2514/2021/06/ZheZhu_CCDC.pdf
relations:
- type: REQUIRES_OBSERVATION
  target: observation:optical-vegetation-state
  status: candidate
  sources:
  - https://gerslab.cahnr.uconn.edu/wp-content/uploads/sites/2514/2021/06/ZheZhu_CCDC.pdf
- type: REQUIRES_VALIDATION
  target: validation:forest-evidence
  status: candidate
  sources:
  - https://doi.org/10.1080/01621459.1993.10476408
---

A proposed median/MAD anomaly rule with a minimum effect size and missing-data guards. Literature supports robust scale and temporal QA concepts, not these NDVI cutoffs. All k/noise-floor/effect/min-count choices require validation. Applicable only to calibrated, quality-masked comparable references; no road label, probability or legal inference follows. Review questions: reference sampling bias, small-sample uncertainty, seasonal alignment and independent holdout design. Contradictions: no external labels; baseline/method valid support differs. Run results remain threshold_experiments.json and persistence_experiment.json in review evidence, not graph facts. Geography/time scope: method proposal generic; execution evidence limited to this Estonia AOI and 2025/2026 summer scenes.
