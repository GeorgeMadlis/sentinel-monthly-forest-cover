# Optional GEE reference/example implementation

Not required for the regional production Python pipeline. These are preserved historical
scripts for formula comparison, annual/global demonstrations and exploratory calculations.
Install `requirements.txt` here separately and authenticate Earth Engine before using them.
Run these scripts directly so their historical `common.py` resolves in this directory.
Original script names and flags are preserved. Existing historical maps remain in `runs/`.

Known differences from production: end-date exclusion, cloud-probability join, broad SAR
geometry mixing, bestEffort reductions, scale-dependent connected components, and no
complete item inventory. See `docs/migration.md` at repository root for equivalence limits.
Do not treat these outputs as monthly ground truth, legal deforestation or causal labels.
