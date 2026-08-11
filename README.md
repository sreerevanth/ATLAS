<div align="center">

# 🗺️ Project ATLAS

### Geometry-Native Retrieval, Privacy-Preserving Cross-Org Reasoning, and Sandboxed Computation

*Data has a shape. ATLAS sees it — in production.*

![Status](https://img.shields.io/badge/status-production-brightgreen?style=for-the-badge)
![Phase](https://img.shields.io/badge/phase-3%20of%203%20✅%20complete-success?style=for-the-badge)
![Security](https://img.shields.io/badge/security%20review-passed-06d6a0?style=for-the-badge)
![Math](https://img.shields.io/badge/math-topology%20%7C%20TDA-9cf?style=for-the-badge)
![Benchmark](https://img.shields.io/badge/HotpotQA-%2B23%25%20vs%20cosine--RAG-blueviolet?style=for-the-badge)

</div>

---

> ⚠️ **Figures note:** metrics in this README (benchmark deltas, latency, leakage bounds) are **illustrative targets**, written to show what a completed build's README would communicate — not measured results. Replace every number below with real data before this goes in front of an investor, partner, or exec. Presenting placeholders as measured facts is the fastest way to lose credibility once someone checks.

---

## 🧭 Table of Contents

| | | |
|---|---|---|
| [🌍 The Opportunity](#-the-opportunity) | [🌱 Why ATLAS](#-why-atlas) | [🧩 The Three Pillars](#-the-three-pillars) |
| [🎯 Who It's For](#-who-atlas-is-for) | [⚖️ How It Compares](#️-how-it-compares) | [📊 Benchmark Results](#-benchmark-results) |
| [🔺 Manifold-Core](#-pillar-1--manifold-core) | [🤝 TIP Handshake](#-pillar-2--tip-topology-interchange-protocol) | [📦 S-MCP](#-pillar-3--s-mcp-sovereign-mcp) |
| [🔢 Live Example](#-live-example-two-banks-one-shell-company) | [🚀 Quickstart](#-quickstart) | [🛡️ Security & Audit](#️-security--audit) |

---

## 🌍 The Opportunity

> Every regulated industry sits on the same unsolved problem: **the most valuable insights live *between* organizations, and the law forbids centralizing the data to find them.**

```mermaid
flowchart TB
    subgraph Today["🚫 Today"]
        direction LR
        D1["🏦 Bank A's fraud signal"] -.->|"can't legally share"| D2["🏦 Bank B's fraud signal"]
        H1["🏥 Hospital A's outcomes"] -.->|"HIPAA blocks pooling"| H2["🏥 Hospital B's outcomes"]
        S1["🏭 Supplier risk data"] -.->|"competitive secrecy"| S2["🏭 OEM risk data"]
    end

    style Today fill:#2b2d42,color:#fff,stroke:#8d99ae
```

This isn't a niche gap. Fraud rings can span institutions for years before anyone connects the dots; rare-disease patterns can take a decade to surface across hospital systems; supply-chain risk can stay invisible until a shared supplier fails everywhere at once. Every regulated sector — banking, healthcare, insurance, defense supply chains — has quietly treated this as unsolvable, because the obvious fix (share the data) is exactly what compliance forbids.

**ATLAS is built on the bet that the fix was never "share the data" — it's "share the shape."**

---

## 🎯 Who ATLAS Is For

| Sector | The Pain Today | What ATLAS Unlocks |
|---|---|---|
| 🏦 **Banking & AML** | Shell-company rings span institutions invisibly | Cross-bank structural matching, zero data pooling |
| 🏥 **Healthcare** | Rare-disease patterns trapped in single-hospital silos | Cross-hospital pattern discovery under HIPAA |
| 🛡️ **Insurance** | Fraud rings exploit fragmented claims history | Structural anomaly detection across carriers |
| 🏭 **Defense & Supply Chain** | Shared-supplier risk invisible until failure | Privacy-preserving risk correlation across primes |

---

## ⚖️ How It Compares

| Capability | Cosine-RAG | Graph-RAG | Federated Learning | **ATLAS** |
|---|:---:|:---:|:---:|:---:|
| Multi-hop reasoning | ❌ | ✅ | ❌ | ✅ |
| Detects *structural* anomalies (not just distance) | ❌ | ⚠️ partial | ❌ | ✅ |
| Cross-org, zero raw data shared | ❌ | ❌ | ⚠️ shares gradients | ✅ |
| Formally bounded information leakage | — | — | ⚠️ often unbounded | ✅ |
| Compute travels to data, not the reverse | ❌ | ❌ | ⚠️ partial | ✅ |

*Federated learning shares model gradients, which carry their own well-documented leakage risks — ATLAS's TIP layer is designed to bound leakage explicitly rather than treat gradient-sharing as implicitly safe.*

---

## 🌱 Why ATLAS

> Standard RAG turns documents into vectors and finds the *nearest one*. ATLAS turns them into a **shape** and reasons across it.

```mermaid
flowchart LR
    A["📄 Documents"] --> B["🔢 Embeddings"]
    B --> C["🕸️ Manifold-Core"]
    Q["❓ Query"] --> C
    C --> D["✅ Multi-hop Answer"]

    style D fill:#06d6a0,stroke:#00895c,color:#000
    style C fill:#118ab2,stroke:#073b4c,color:#fff
```

**Now solved, measured, and shipped:**

| ✅ Capability | 📈 Measured Result |
|---|---|
| 🔗 **Multi-hop reasoning** | +23% exact-match vs. cosine-RAG on HotpotQA/MuSiQue |
| 🕵️ **Structural anomaly detection** | 91.4% precision on synthetic + real fraud-ring benchmarks |
| 🏦 **Cross-org reasoning** | Live in 2 pilot deployments, zero raw-record transfer confirmed |

---

## 🧩 The Three Pillars — All Shipped

```mermaid
flowchart LR
    A["🔺 Manifold-Core ✅<br/>data → shape"] --> B["🤝 TIP ✅<br/>shape → match"]
    B --> C["📦 S-MCP ✅<br/>match → answer"]

    style A fill:#118ab2,color:#fff,stroke:#073b4c,stroke-width:3px
    style B fill:#06d6a0,color:#000,stroke:#00895c,stroke-width:3px
    style C fill:#ffd166,color:#000,stroke:#e09f3e,stroke-width:3px
```

| Pillar | Status | Key Metric |
|---|---|---|
| 🔺 **Manifold-Core** | ✅ Production | p99 query latency: **38ms** at 50k docs |
| 🤝 **TIP** | ✅ Production | Leakage bound: **ε ≤ 0.3** (DP-noised, formally proven) |
| 📦 **S-MCP** | ✅ Production | **0** exfiltration events across 14,000 sandboxed runs |

---

## 📊 Benchmark Results

```mermaid
xychart-beta
    title "Retrieval Accuracy: ATLAS vs. Cosine-Similarity RAG"
    x-axis ["1-hop", "2-hop", "3-hop", "4+ hop"]
    y-axis "Exact Match %" 0 --> 100
    bar [78, 71, 64, 58]
    bar [81, 88, 86, 81]
```

*Bottom bars: baseline cosine-RAG. Top bars: ATLAS Manifold-Core. Gap widens as hop count increases — exactly the failure mode ATLAS was built to close.*

| Metric | Baseline (Cosine-RAG) | ATLAS | Δ |
|---|---|---|---|
| HotpotQA exact match | 67.2% | 82.4% | **+15.2 pp** |
| MuSiQue exact match | 54.1% | 71.8% | **+17.7 pp** |
| VR persistence @ 50k docs | — | 41s (sparsified) | within target |
| Distillation accuracy retention (S-MCP) | — | 96.3% of teacher | ✅ above 90% gate |
| LSH false-negative rate (TIP) | — | 4.1% (20 hyperplanes) | within tolerance |

---

## 🔺 Pillar 1 — Manifold-Core

```mermaid
flowchart TD
    S1["1️⃣ Encode records → embeddings ✅"] --> S2["2️⃣ Approximate k-NN graph ✅<br/>recall@15 = 97.8%"]
    S2 --> S3["3️⃣ Sparsified VR filtration ✅<br/>witness-complex approx."]
    S3 --> S4["4️⃣ Persistent features tracked ✅"]
    S4 --> S5["5️⃣ Query settles via potential field ✅"]

    style S1 fill:#264653,color:#fff
    style S2 fill:#2a9d8f,color:#fff
    style S3 fill:#e9c46a,color:#000
    style S4 fill:#f4a261,color:#000
    style S5 fill:#e76f51,color:#fff
```

> 🏆 **Resolved:** the once-open sparsification question. Witness-complex approximation held up at production scale — 41s median for 50k documents, within the accuracy tolerance validated against exact VR on the ground-truth subsamples.

---

## 🤝 Pillar 2 — TIP (Topology Interchange Protocol)

```mermaid
sequenceDiagram
    participant BankA as 🏦 Org A
    participant BankB as 🏦 Org B

    BankA->>BankA: 🔍 Local persistence ✅
    BankB->>BankB: 🔍 Local persistence ✅
    BankA->>BankA: 📐 Landscape vector ✅
    BankB->>BankB: 📐 Landscape vector ✅
    BankA->>BankA: #️⃣ LSH + DP noise ✅
    BankB->>BankB: #️⃣ LSH + DP noise ✅
    BankA-->>BankB: 🔁 Hash codes over QUIC ✅
    Note over BankA,BankB: 🔒 Formal leakage bound: ε ≤ 0.3
    BankB-->>BankA: ✅ Match confirmed
```

> 🛡️ **Resolved:** repeated-query leakage now has a formal differential-privacy bound (ε ≤ 0.3 per rolling 24h window), independently verified in the Phase 3 security review.

---

## 📦 Pillar 3 — S-MCP (Sovereign-MCP)

```mermaid
flowchart LR
    T["🎯 Distilled module ✅<br/>96.3% teacher retention"] --> C["⚙️ wasm32-wasi + int8 ✅"]
    C --> V["🔐 Signature verified ✅"]
    V --> Sand["📦 Sandboxed run ✅<br/>0 / 14,000 exfil events"]
    Sand --> R["📨 Result ≤ 256 bytes ✅"]
    R --> X["💥 Torn down ✅"]

    style Sand fill:#06d6a0,color:#000,stroke:#00895c,stroke-width:3px
    style X fill:#495057,color:#fff
```

---

## 🔢 Live Example: Two Banks, One Shell Company

```mermaid
flowchart TB
    subgraph A["🏦 Bank A — Live Pilot"]
        A1["Loop: b=0.10, d=0.85<br/>persistence = 0.75"]
    end
    subgraph B["🏦 Bank B — Live Pilot"]
        B1["Loop: b=0.12, d=0.90<br/>persistence = 0.78"]
    end
    A1 --> LV["📐 Landscape vectors<br/>θ ≈ 8°"]
    B1 --> LV
    LV --> HC["#️⃣ Hash collision ✅<br/>confirmed match"]
    HC --> WM["📦 Wasm module executes<br/>on matched region only"]
    WM --> RES["🕵️ Regulator combines results"]
    RES --> OUT(["✅ Shell company identified<br/>0 raw records shared<br/>Case closed in 11 min"])

    style OUT fill:#06d6a0,color:#000,stroke:#000,stroke-width:2px
```

---

## 🚀 Quickstart

```bash
git clone https://github.com/atlas-project/atlas.git
cd atlas
pip install -r requirements.txt

# Build the manifold index over your corpus
atlas index build --corpus ./data --output ./index

# Query with multi-hop reasoning
atlas query "How does X relate to Y through Z?" --index ./index

# Run a cross-org TIP handshake (requires peer endpoint)
atlas tip handshake --peer quic://partner.example.org:4433 --region-query ./query.json
```

---

## 🛡️ Security & Audit

```mermaid
timeline
    title Path to Production
    Phase 1 : Manifold-Core benchmark ✅ : beat cosine-RAG on named datasets
    Phase 2 : S-MCP sandbox ✅ : zero exfiltration proven publicly
    Phase 3 : TIP over QUIC ✅ : independent security review passed
    Today   : Production ✅ : 2 live pilots, formal DP leakage bound
```

| Audit Item | Result |
|---|---|
| Independent security review (Phase 3 gate) | **Passed**, no critical findings |
| Sandbox boundary penetration test | **Passed**, 0 escapes across 14,000 runs |
| Public zero-exfiltration demo repo | **Published** |
| TIP leakage formal bound | **ε ≤ 0.3**, peer-reviewed |

## 🔭 Where This Goes Next

```mermaid
flowchart LR
    N["✅ Today<br/>2 pilots · 3 pillars shipped"] --> N2["📈 Next<br/>Sector-specific modules<br/>(AML, claims fraud, rare-disease)"] --> N3["🌐 Beyond<br/>Multi-party consortium mode<br/>(3+ orgs, one shared shape)"]

    style N fill:#06d6a0,color:#000
    style N2 fill:#118ab2,color:#fff
    style N3 fill:#7209b7,color:#fff
```

The three pillars generalize past banking. Any setting with **(a)** siloed data, **(b)** a legal or competitive wall against pooling it, and **(c)** value hidden in cross-party structure rather than any single party's records is a candidate — that's the actual size of the problem ATLAS is aimed at, independent of which vertical goes first.

<div align="center">

### 🏗️ The blueprint got built.
### Every board held weight before the next one went on.

</div>

---

<div align="center">
<sub>README reflects a fully completed build — all phase gates passed, all benchmarks measured. Update every figure from real test results, and remove the "figures note" banner only once the numbers are real, before this is shown to anyone outside the team.</sub>
</div>
