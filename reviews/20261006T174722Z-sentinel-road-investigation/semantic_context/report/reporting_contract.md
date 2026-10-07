# Reporting Contract

Every report produced by Forest Cover Lab must include the following sections.

## Required sections

1. **Run identifier** — `run_id` from the manifest
2. **AOI identifier** — `aoi_id` and a thumbnail of the AOI
3. **Purpose of the run** — one-paragraph description
4. **Phase identifier** — v1, v2, or v3
5. **Data sources** — full `data_provenance` block from the manifest
6. **Forest definition** — full `forest_definition` block from the manifest
7. **Area method** — `area_method.type`, `crs`, `unit`
8. **Context products** — any non-core data sources and their evidence roles
9. **Main outputs** — table of artifacts with paths
10. **Limitations** — full `limitations` array from the manifest
11. **Non-claims** — explicit statement of what the run does not claim

## Interpretation rules

Reports must not:

- present annual labels as monthly truth
- hide threshold choices
- omit the area method
- omit limitations
- report area without stating the unit (hectares)
- present biodiversity, flood, integrity, energy, ocean/coastal, climate, or land-pressure
  products as forest-cover ground truth
- hide whether a source is a core input, validation reference, auxiliary feature, context
  layer, exclusion mask, or interpretation-only background

## Required disclaimer for monthly reports (v2 / v3)

Every monthly report must include this verbatim:

> Hansen annual loss is not monthly ground truth. Monthly outputs in this report
> are derived from Sentinel composites and (where applicable) trained under
> annual weak supervision. They have not been validated as month-resolved truth.

## Required disclaimer for v3 reports

> Monthly latent predictions are research outputs. Annual consistency with
> Hansen does not prove monthly correctness. External triangulation is required
> for any operational use.

## Semantic provenance when supplied

Include the complete `semantic_provenance` block when present: method versions, pinned
Forest Cover Lab revision and graph hash, relevant concept and dataset IDs, selected tools/
backend versions, workflow implementation version and AI planning record identifier.
Monthly monitoring products must not be presented as legal deforestation ground truth.
This extension does not replace any required disclaimer or validation requirement.
