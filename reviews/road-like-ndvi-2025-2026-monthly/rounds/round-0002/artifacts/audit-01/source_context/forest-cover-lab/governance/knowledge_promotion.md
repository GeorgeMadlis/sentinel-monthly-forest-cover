# Knowledge promotion and AI extraction

Source / paper / experiment → contextual OKF-oriented record → candidate relation →
deterministic checks plus scientific validation and human review → authoritative relation.

AI extraction always starts with `status: candidate` on concepts and relationships. Keep
source identity, limitations and explanatory context. An extraction or a single workflow
run cannot silently mutate canonical concepts, validated edges, thresholds or claims.
Runtime planning records and evidence are downstream artifacts, never automatic graph edits.

Promotion is a reviewed repository change. Reviewers check the original evidence, scientific
meaning, temporal/geographic applicability, confounders, dataset roles and non-claims. Any
performance or threshold claim needs a documented validation artifact with uncertainty.
Deterministic checks establish syntax and referential integrity; they cannot establish
scientific correctness. A human scientific reviewer records `review.by`, `review.date` and
`review.basis` with sources supporting the exact assertion before changing a candidate edge
to validated. Endpoints must be active; unsupported edges stay candidates or are removed.
Run graph generation, tests and drift review; pin the resulting commit and graph hash.

The initial validated edges explicitly use `repository-contract-transcription` as their
review attribution: they reproduce existing contract requirements or documented API
capabilities, not experimental outcomes or purported human endorsement. The new seasonal
and intended downstream mappings remain candidates. Any expansion beyond those source
meanings must go through the promotion process above.

A deprecated concept is retained for stable reference but cannot have new validated edges.
Review deadlines trigger assessment; they never cause automatic promotion. Maintainers
control canonical updates through version control and review. Downstream descriptors cannot
change canonical semantics by declaring a divergence.
