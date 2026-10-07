# Data Source Notes

Qualitative notes per data source. One section per entry keyed to `inventory.csv` IDs.
Add a section when a source requires more context than fits in the CSV `notes` field.

---

## DS-0001 — Hansen GFC v1.12

The foundational v1 dataset. Key implementation details:

- `treecover2000` is the percentage canopy cover in the year 2000. It does not update annually.
- `lossyear` encodes the year of first canopy loss, not cumulative or recurring loss.
- `datamask` must be used to exclude water and uncharacterized land (only `datamask == 1`
  qualifies as mapped land; see ADR 0002).
- The dataset is updated annually but the `treecover2000` band is frozen at the 2000 baseline.

**v3 weak supervision caution:** `lossyear` is annual by construction. Using it as a monthly
target variable without temporal disaggregation violates the non-claim stated in the repo
README and ADR 0004.

---

## DS-0002 — Sentinel-2 MSI L2A

The core v2 optical input. Key implementation details:

- The `COPERNICUS/S2_SR_HARMONIZED` collection in GEE harmonizes L1C-era and L2A-era data.
- Preferred cloud masking: `s2cloudless` (probabilistic) or the `SCL` quality band
  (class 4 = vegetation, class 5 = bare soil, class 6 = water, class 8/9 = clouds/shadows).
- Monthly compositing: use median or percentile composites over all clear-sky acquisitions
  within a calendar month. Record the number of clear observations per pixel in the manifest.
- Temporal gap: pre-2017 data is not available. For AOIs requiring longer baselines,
  supplement with Landsat (DS-0004).

---

## DS-0003 — Sentinel-1 GRD

The cloud-robust v2 complement. Key implementation details:

- GEE provides border noise correction and thermal noise removal in the `COPERNICUS/S1_GRD`
  collection as of 2021. For earlier acquisitions, verify noise correction status.
- VV+VH dual-polarization is standard for forest monitoring. VH backscatter is more
  sensitive to canopy structure than VV.
- Speckle filtering (e.g. refined Lee, Gamma-MAP) is required before compositing.
- Terrain correction is critical in mountainous regions; GEE applies basic Range-Doppler
  correction but this may be insufficient for steep terrain.
- Backscatter is sensitive to soil moisture — wet season vs. dry season differences can
  mimic deforestation signals. Temporal averaging reduces this artefact.

---

## DS-0007 — JRC Tropical Moist Forest (TMF)

Independent cross-validation source for tropical AOIs. Key notes:

- TMF uses a different forest definition from Hansen GFC — it is calibrated to the humid
  tropics and distinguishes deforestation from degradation.
- Comparison with Hansen GFC for the same AOI should expect systematic differences due to
  definition, not errors in either product.
- Geographic scope is pan-tropical (not global). Not suitable for temperate or boreal AOIs.
- Annual class transitions (undisturbed / disturbed / deforested / regrowth) are more
  granular than Hansen's binary lossyear.

---

## DS-0009 to DS-0013 — Context product placeholders

These rows reserve the architecture for adjacent Earth-observation context products. Replace
each placeholder with a reviewed product only after recording a search scope and completing
the suitability assessment.

Context entries must answer:

- What forest-cover interpretation problem does this product help with?
- Is the product a core input, auxiliary feature, validation reference, context/risk layer,
  exclusion mask, or interpretation-only background?
- Could using this product create circular evidence because it already includes land cover
  or forest information?
- What claims must reports avoid when referencing this product?
