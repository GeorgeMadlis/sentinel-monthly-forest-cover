# Execution workflow

1. Supply a versioned external forest baseline, AOI and schema 2.0 workflow.
2. Declare calibrated optical assets and pixel quality, comparable SAR acquisition
   geometry, thresholds and fusion rules. Start with a small validated AOI.
3. Run `scripts/run_pipeline.py` using the README command.
4. Inspect inventories/count rasters, nodata/coverage, disagreement and quicklooks.
5. Review provisional candidates against independent evidence and reconcile annually.

Stages can also be run separately, in this order, with the same arguments:
`build_monthly_composites.py`, `compute_ndvi_anomaly.py`, `estimate_loss_area.py`,
`export_reporting_artifacts.py`. They exchange durable rasters and the discovery
inventory. The output directory rejects a changed config/AOI; use a new prefix.
`render_final_map.py` refreshes reporting after area estimation. Historical annual GEE
assessment is now an explicit reference example.

## Temporal modes

Date-only configured start/end are inclusive. Generated inventory/manifest windows are
**half-open UTC** `[start,end)`; unlike the historical GEE end date, the last day is
included. All reference periods precede the target.

- `monthly`: full calendar month with corresponding full reference months in previous
  years; leap-month lengths may differ. Current aggregation defaults must be declared.
- `moving-window`: `window_days`, `step_days`, `alignment: relative-day`; reference
  periods have equal duration. Corresponding offsets are compared. Only complete
  windows are emitted; a short trailing fragment is omitted.
- `matched-season`: `alignment: calendar-date`; reference start/end month/day match
  target endpoints. Seasons are user-defined, including Southern Hemisphere and
  cross-year periods. No hemisphere is inferred.
- `matched-season-moving-window`: complete moving windows within matched periods;
  endpoints align by calendar date. An unavailable February 29 fails rather than shifting.

`aggregation: mean|median` applies per feature within each period. SAR may override it.
`reference_statistic: period-composites` gives each reference period equal weight:
mean and population standard deviation of its composites, after minimum observation
checks. `pooled-observations` uses mean/std of all unique reference observations and
preserves legacy anomaly baseline semantics. These are scientifically different choices.
With only one valid reference composite standard deviation is zero; sigma decisions
then reduce to strict negative change. Prefer fixed validated thresholds or additional
reference periods, and inspect observation-count evidence. Indicators use all configured
features as an AND rule with separate names/thresholds; NDVI/NDMI/NBR are not interchangeable.

Overlapping windows each get their own area summary; they are never summed into unique
loss area. `loss_area_summary.json` retains legacy top-level month/area fields for a
single-window run. Multi-window runs use the explicit `windows` array.

Fusion modes are `optical_only`, `sar_only`, `optical_and_sar`, `optical_or_sar`, and
`weighted_confidence`. Combined modes require both valid sensors per pixel. Weights
must be nonnegative and sum to one. Agreement/disagreement requires both sensors;
missing evidence is nodata rather than agreement or absence. Forest gating occurs
before fusion. Minimum mapping-unit filtering affects final disturbance, while raw
fused candidates and disagreement remain available for diagnosis.
