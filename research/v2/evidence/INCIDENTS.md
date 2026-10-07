# Recorded pre-final incidents and amendments

The first scaling invocation used code commit5e0e6db and completed all24
resource-bounded topology workers. Their original outputs remain under `scaling/`.
Its aggregation did not finish in a practical time: Persim's Python bottleneck
comparison consumed several minutes of CPU after the final worker completed.
The specific scaling process was stopped. No final retrieval evaluation had run.

The replacement uses GUDHI's exact bottleneck distance (`e=0`) on the SAME
finite-bar comparison definition. It reruns every worker into `scaling-gudhi/`
with a new manifest; no fastest-run or favorable-distance selection is performed.
Wasserstein remains Persim. Essential interval counts remain separate. The
uncompleted first aggregation is not scientific evidence of topology failure.

Before final configuration freeze, source-only amendments added replay support,
missing-ignored-cache handling for fresh clones, provenance checks, an API that
bypasses experimental machinery for cosine, and generated reporting. No ranking
function, ablation grid, validation threshold, or split was changed after seeing
development or validation outcomes. V1 protected bytes were not changed.

On a fresh clone, the protected inventory contains ignored generated egg-info
as well as ignored research artifacts. Explicit missing-artifact allowance covers
these absent generated files only. Present files with mismatched bytes still
fail; absence is recorded, not presented as a successful126-file verification.
