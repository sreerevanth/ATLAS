# Research execution record

This record separates completed local experiments from remaining research.
Historical reports are not used as evidence. Run artifacts under `artifacts/local/`
are generated and ignored by Git so datasets and outputs
do not accidentally enter a source release. Keep each run directory with the
source commit and raw results when archiving evidence.

## Environment and commands

- Reference interpreter: Python 3.12.4, Windows 11, AMD64 Family 25 Model 80,
  16 logical CPUs, 16.5 GB installed RAM; CPU only; seed 42.
- Source baseline: `c8bf38a`; all new research code remains uncommitted at report
  time. Each per-command manifest contains source SHA-256 values and dirty Git
  status. Commands run from `.venv-release` for final scaling/retrieval artifacts.
- Package versions are captured by each run manifest and `requirements-lock.txt`.
- `python -m pytest -q`: 12 passed in the clean Python 3.12 environment.
- `python -m ruff check src tests`: passed.
- `python -m atlas validate --output artifacts/local/validate`: passed.
- `python -m atlas integration --output artifacts/local/integration`: passed;
  synthetic local QUIC OFFER/MATCH and signed Wasm EXECUTE/RESULT completed.
- `python -m atlas tip --output artifacts/local/tip`: completed synthetic sweep.
- `python -m atlas anomaly --output artifacts/local/anomaly`: completed synthetic
  relational anomaly run.
- `python -m atlas corpus --output artifacts/local/research`: completed on the
  pinned HotpotQA dev distractor validation split.
- Corpus count: 7,405 available questions; 1,500 sampled; 14,930 document
  occurrences; 14,568 cleaned documents; 362 exact duplicates; zero invalid,
  empty, near-empty or missing-support exclusions. Raw Parquet SHA-256 is
  `c20b638ca82b21d04fe12e14ff417ad05153d4d215a65de54497fca4e972f7c6`.
- Embeddings: `sentence-transformers/all-MiniLM-L6-v2` revision
  `c9745ed1d9f207416be6d2e6f8de32d1f16199bf`, dimension 384, CPU, batch 64.
  Encoding took 541.69 seconds at 29.66 texts/second; repeated subsample max
  absolute difference was 0.0. The model truncates at 256 tokens without chunking.
- `python -m atlas ann --output artifacts/local/research`: completed 24 exact vs
  HNSW parameter combinations against exact cosine top-15 for 300 queries. Recall
  ranged from 0.7729 to 0.9978. At M=32, efConstruction=100, efSearch=128, recall
  was 0.9978; build took 4.87 seconds, p50/p95/p99 query times were 0.514/0.825/
  0.970 ms, serialized size 26,341,186 bytes, and sampled peak RSS growth 26,193,920
  bytes. Raw per-query outputs and all settings are in `artifacts/local/research/ann.json`.
- `python -m atlas handcrafted --output artifacts/local/handcrafted`: passed
  five seeded source-bridge-answer cases; cosine top-3 missed the complete chain.
- `python -m atlas scaling --output artifacts/local/research`: completed 24 rows:
  exact VR and greedy landmark VR at 250/500/1,000, plus landmark VR at 2,000,
  5,000 and 10,000 (exact above 1,000 skipped by predeclared resource policy).
  At 1,000 points, exact took 2.35 s with 488,335 edges; 32 landmarks took
  0.042 s with 455 edges, but H0/H1 bottleneck distances were 0.5874/0.0736 and
  Wasserstein distances 675.57/55.59. Largest finite H1 lifetime changed from
  0.1472 to 0.0399. This is a runtime/memory trade-off with material topology
  loss, not validation that the approximation preserves useful topology. The
  resource-capped scale run did not attempt exact beyond 1,000 points.
- `python -m atlas retrieval --output artifacts/local/research`: completed 300
  paired HotpotQA sampled-distractor questions, 6 retrieval configurations and
  1,800 question/config rows. Cosine all-support@5 was 0.4933; ATLAS was 0.4833.
  Paired delta (ATLAS minus cosine) was -0.0100 with a question-bootstrap 95% CI
  of [-0.0267, 0.0033]; GO=false. This does not show a retrieval benefit. The
  bootstrap treats questions as units despite shared source documents, so the
  interval may be too narrow. The result is a sampled validation subset, not the
  full official test protocol; no generation metric was evaluated.
- Retrieval ablations on the same subset: graph-only all-support@5 0.4900,
  topology-only 0.5000, ATLAS 0.4833, low-weight ATLAS 0.4933, high-weight ATLAS
  0.4767. No result establishes a consistent or statistically supported benefit.

## Topology gate

Ripser computed a 100-point circle and its seeded noisy counterpart. Each diagram
had one H1 interval above the predeclared 0.5 lifetime threshold. The two tight
clusters had one essential H0 interval and one finite H0 interval with death above
1.0, consistent with two components across a separating scale. Full diagrams and
seeded gate observations are in `artifacts/local/validate/topology_gate.json`.
This validates these fixtures only; it does not validate embedding topology.

## Exact versus landmark persistence

Exact VR and Ripser greedy-permutation landmarks used identical prefixes of the
same normalized document embedding array, in isolated workers with a 1.5 GiB
cap, a 120-second timeout and sampled aggregate launcher/descendant RSS (25 ms
interval; brief peaks can be missed). Finite and essential intervals are
preserved in JSON (`null` death denotes infinity); persim computes diagram
distances with its documented treatment of essential intervals. At 1,000 points,
32 landmarks reduced measured persistence time from 2.35 s to 0.042 s and edge
count from 488,335 to 455, while H0/H1 bottleneck distances were 0.5874/0.0736.
The largest finite H1 lifetime fell from 0.1472 to 0.0399. Even 128 landmarks
had H0/H1 bottleneck distances 0.5682/0.0736 and largest finite H1 lifetime
0.0784. This is not a witness complex and is not faithful enough here to support
the proposed topology-aware retrieval without further method development.

The exact runs are feasible only through 1,000 points under the configured
policy. Greedy landmark runs reached 10,000 points with 128 landmarks in 1.16 s
of persistence computation and sampled process-tree RSS of about 197 MiB, but
larger-N exact comparisons were intentionally not performed. These runtime
numbers do not justify extrapolating fidelity or release-scale feasibility.

## External retrieval GO/NO-GO

On 300 seeded questions from the pinned HotpotQA dev distractor pool and identical
frozen embeddings/corpus, cosine scored 0.730 supporting-title recall@5 and 0.4933
all-support@5. The primary ATLAS density-plus-local-persistence traversal scored
0.7233 and 0.4833. The paired all-support@5 difference was -0.0100
(question-bootstrap 95% interval [-0.0267, 0.0033]); the preregistered lower-bound
GO condition failed. Graph-only, topology-only, low-weight and high-weight
ablations scored 0.4900, 0.5000, 0.4933 and 0.4767 all-support@5 respectively.
These data do not show a reliable advantage over cosine, so the central retrieval
claim is NO-GO. The interval resamples questions although pooled contexts share
documents; a cluster-aware analysis is still needed. This is retrieval-only on a
sampled dev distractor pool, not generation quality or fullwiki evaluation.

The [HotpotQA dataset card](https://huggingface.co/datasets/hotpotqa/hotpot_qa)
identifies the dataset as CC BY-SA 4.0; the license and pinned revision are also
recorded in generated corpus metadata. The metadata produced by the earlier corpus
run predates addition of the explicit license field; rerunning `corpus` refreshes it.

## Synthetic TIP signature classification

The tested positive pairs compare a unit circle with independently perturbed
copies; negatives compare the circle with an unrelated uniform square cloud.
There are 20 positive and 20 negative pairs per parameter setting. Resolution,
hyperplane count, Gaussian noise scale and threshold are swept. These are
signature-matching classification rates, not a privacy or real-world accuracy
claim. Full rows and pair scores are in `artifacts/local/tip/tip.json`.
At 64 hyperplanes and threshold 0.75, the 20 positive pairs had false-negative
rates 0, 0, 0, 0.35 and 1.0 at noise scales 0, 0.03, 0.08, 0.15 and 0.3;
all 20 negative pairs stayed below threshold in each setting. This narrow
synthetic separation does not imply a negligible miss rate under noise.

## Synthetic relational anomaly

Forty seeded graphs contain two random within-block graphs and six planted
cross-block cycle nodes; features are independently random. At the selected
95th percentile threshold over normal structural scores, the structure score
achieved precision 0.1582, recall 1.0, F1 0.2732, AUROC 0.8005 and AUPRC 0.1582.
The feature-only control achieved AUROC 0.4876 and AUPRC 0.0704. The low precision
is material: most alerts at this threshold are false positives. This is one
synthetic construction, not evidence of fraud detection. Raw labels and scores
are in `artifacts/local/anomaly/anomaly.json`.

## Local integration

Two in-process nodes used synthetic normalized Gaussian vectors. A local QUIC
stream carried an OFFER and a MATCH, followed by an EXECUTE containing a signed
Wasm module. The node copied only the matched local embedding rows into Wasm memory;
the module summed the bytes and returned one signed 32-bit integer. The run found
one local region. It used an ephemeral self-signed certificate and disabled
certificate verification for loopback, so it proves neither peer identity nor
privacy/security in deployment. Raw event measurements are in
`artifacts/local/integration/integration.json`.

## Remaining research gaps

MuSiQue/full HotpotQA replication, cluster-aware confidence intervals, retrieval
seeds beyond the deterministic encoder/index path, scaling beyond 10,000 points,
a scientifically stronger witness/sparse method, real-data anomaly evaluation,
and remote authenticated TIP/S-MCP deployment remain unexecuted. The TIP pair
sweep and anomaly result remain synthetic only. These gaps limit release claims.
