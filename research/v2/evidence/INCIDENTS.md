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

## Post-final resource instrumentation finding

The forensic check found another error: Windows virtualenv launches a small
parent process and a separate native Python interpreter. Both original scaling
runs sampled only the parent. Their RSS values are invalid and must not be cited.
The final retrieval code, configuration and outputs are preserved unchanged.

`python -m tools.verify_v2_release measure` is a separate corrected measurement runner
that samples and limits the entire process tree. It repeats ALL topology cells,
checks equality of resulting diagrams against the original diagrams, and records
new manifests, timings and RSS. This is resource remeasurement, not final-test
retrieval re-evaluation. The corrected publication command replaces the original
memory table and plot with these measurements. Keeping the frozen retrieval
source intact makes the final experiment commit directly replayable.
