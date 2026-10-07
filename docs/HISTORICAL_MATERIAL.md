# Historical material and current sources of truth

Historical files are retained in place and in Git history for attribution and
provenance. A historical label is not a judgment about a contributor. It prevents
plans, illustrative outputs and superseded interpretations from being presented
as current experimental findings.

## Current research record

- `README.md`: evidence-first entry point, generated numeric tables.
- `CLAIMS.md`: supported claims and explicit non-claims.
- `MANIFOLD_V2_REPORT.md` and `research/v2/evidence/`: frozen V2 findings.
- `MANIFOLD_V1_NO_GO.sha256.json`: frozen V1 byte inventory.
- `RESEARCH_REPORT.md`: preserved V1 execution snapshot. Its uncommitted-code
  wording and remaining-work list describe that earlier moment, not current V2.
- `IMPLEMENTATION_AUDIT.md`: baseline forensic audit, not a claim that later
  experimental capability gaps have all been resolved.
- `adrs/ADR-003-research-reset.md` and `adrs/ADR-004-v2-evidence-gated-retrieval.md`:
  evidence-driven architecture decisions.

## Retained historical design / specification

`MASTER_PLAN.md`, `ATLAS_PROMPT_BOOK.md`, `ATLAS_TECHNICAL_README (1).md`,
`01_core_principles.md`, `pr11.md`, `adrs/ADR-001_persistence_landscapes.md`,
`adrs/ADR-002_privacy_layer.md`, `adrs/Phase20_Final_ADR.md`, and `specs/`
are historical planning/design context. Proposed phases and mathematical or
security assertions are not implementation, deployment or validation evidence.

In particular, phase12–19 headings do not establish production readiness,
clinical pilots, regulatory authorization, zero knowledge, post-quantum security,
global federation or hardware acceleration. All19 triaged PRs were closed
without merging; authorship and discussion remain available in their PR history.

## Retained legacy experiments and drafts

- `atlas-core/`: earlier SDK/prototypes. Its former privacy-preserving SDK and
  package-install language is historical, not current release guidance.
- `atlas-experiments/`: historical experiment descriptions, scripts and reports.
  Their standalone numbers are not accepted release evidence.
- `papers/paper-A/main.tex`, `papers/paper-B/main.tex`: explicitly marked
  historical, unvalidated drafts. Their illustrative author/consortium metadata
  and publication-style prose do not establish a real consortium, peer review,
  publication, empirical result or privacy guarantee.
- Legacy root scripts, report generators, Docker/manifests and demonstrations
  remain inspectable, but are outside the verified `src/atlas` / `research/v2`
  implementation unless specifically identified in the current evidence report.

No historical document or frozen evidence file was deleted to hide a result.
Generated caches and databases remain ignored rather than release artifacts.
