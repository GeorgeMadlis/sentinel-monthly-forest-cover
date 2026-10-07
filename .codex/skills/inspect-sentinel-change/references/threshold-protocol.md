# Threshold experiment protocol

Use this protocol in visual analysis; let literature refine it, corroboration supply independent labels, and reporting distinguish experiments from validated methods. This is a proposed robust screening experiment, not a published road detector.

## Baselines and common support
Reproduce fixed delta NDVI < -0.2 and sigma delta < -k*s using current manifests; the documented defaults are k=2, VV drop >1.5 dB, VH drop >1.0 dB with strict inequalities. Confirm actual implementation. Preserve positive-standard-deviation and minimum-count requirements. Fixed and sigma reference populations differ. Compare each fusion pair on its own common valid support, then all methods on an explicit shared intersection. Report unavailable area separately. Never fill unavailable with zero.

## Robust reference alternative
For calibrated per-scene NDVI stack x_i, calculate per pixel m=median(x_i), MAD=median(abs(x_i-m)), s_r=1.4826*MAD, z_r=(m-target)/max(s_r,epsilon). Candidate requires at least five clear, unique reference dates, z_r > k AND m-target > delta_min. Five is an experimental guardrail, not proof of statistical adequacy. Missing target or inadequate count is unavailable. Reject invalid NDVI/calibration before estimation. The 1.4826 factor is a normal-consistency convention, not a normality guarantee. epsilon is a declared empirical noise floor, not a device to manufacture significance. This is a robust anomaly score, not a p-value.

Use k in {2,2.5,3}, delta_min in {0.1,0.15,0.2}, epsilon in {0.02,0.05} as a declared illustrative sensitivity grid; adapt from evidence before viewing held-out labels. Record all attempted settings, do not select the most road-like result. Check whether best-ranked clear scenes censor variability; describe seasonal mismatch. Apply the supplied pure-array helper tile by tile inside existing pipeline abstractions, not by loading an entire country stack.

## Persistence and fusion
Where at least three distinct clear target acquisitions exist, test negative changes recurring on at least two independent dates with explicit spacing, coverage and season matching. Overlapping composites sharing scenes are not independent dates. Do not invent persistence from the one 20 June image. Obtain additional AOI windows through existing access logic if feasible. Preserve date-level evidence and detection interval.

Compare optical-only, paired-valid AND, paired-valid OR and discordance under identical masks. Explore VV/VH signed changes and threshold grids around recorded defaults; retain reasons why radar may increase, decrease or show mixed-pixel nonresponse. Weighted candidate votes remain heuristic scores, not probabilities. Probabilistic fusion requires independent labels, calibration and spatial/temporal holdouts.

Use NDMI/NBR only if required calibrated bands exist, documenting different meanings. Optional line/object screening can measure elongation, connectivity and approximate width; do not use it as a road label. Keep thin linear features when evaluating minimum-mapping-unit effects. Otsu/percentile thresholds may depend on class mixture and are not universal improvements. Longer seasonal-residual/BFAST/CCDC approaches require adequate multi-year time series and diagnostics; do not fit them to eight reference observations and a single target.

## Validation
Run synthetic tests for nodata, insufficient samples, zero MAD/noise floor, strict boundaries and array/grid alignment. Verify mask area on projected equal-area grid, common-support accounting and no mutation of original artifacts. If independent labels exist, lock settings before evaluating spatially separated holdout ROIs, report class imbalance and uncertainty. Without labels, compare sensitivity and stability only. Disclose heuristic thresholds and multiple testing; no false-discovery-rate claims without defensible null probabilities and dependence assumptions.
