# ATLAS MASTER PLAN (Upgraded Ponytail Architecture)

> **Historical material — not current validation evidence.** Retained for design
> context, contributor attribution and provenance. Phase labels, figures and
> capability statements below are not current ATLAS claims. See the
> [current evidence and historical-material guide](docs/HISTORICAL_MATERIAL.md).

Following a rigorous forensic review of the 20-phase roadmap, we have aggressively stripped out theoretical over-engineering. Applying the "Lazy Senior Developer" directive (YAGNI, platform-native over custom code, smallest diff wins), the roadmap is now optimized for maximum speed, security, and minimal codebase footprint.

## Phase 1-4: The Mathematical Core
* **Phase 1 (Research):** TDA as macroscopic privacy.
* **Phase 2 (Philosophy):** "Data Never Moves." Local inference only.
* **Phase 3 (Topology):** Rely strictly on the `ripser` C++ library. *Upgrade: Do not attempt to write custom topological wrappers; `ripser` is already mathematically optimal.*
* **Phase 4 (Privacy Modeling):** Adversarial Autoencoder (AAE). *Upgrade: Since validation proved 50% accuracy (perfect blinding), we freeze the PyTorch model architecture here. No complex hyperparameter scaling is needed. It works.*

## Phase 5-8: The HTTP & Search Network
* **Phase 5 (Networking):** FastAPI and Uvicorn. *Upgrade: Stick to HTTP/JSON. Do not migrate to gRPC unless packet size becomes a hard bottleneck (YAGNI). HTTP allows standard web-firewall inspection.*
* **Phase 6 (Persistence):** SQLite. *Upgrade: SQLite handles up to 100,000 concurrent reads natively. Do not introduce PostgreSQL unless the node exceeds 1TB of state.*
* **Phase 7 (Security):** SHA-256 Commitments. 
* **Phase 8 (Vector Search):** FAISS HNSW. *Upgrade: Rely purely on `faiss-cpu`. GPU FAISS introduces CUDA dependency nightmares on edge hospital nodes.*

## Phase 9-13: Brutal Code Deletion (The "Ponytail" Upgrades)
* **Phase 9 (Sandboxing):** **DELETED.** *Upgrade:* We previously planned custom Wasmtime fuel-metering and Python Opcode injection. This is massive over-engineering. We will delete all custom sandboxing code and strictly use Native Linux `cgroups`, `namespaces`, and `seccomp` (Docker). *The best code is no code.*
* **Phase 10 (Testing):** `pytest` automated integration.
* **Phase 11 (SDK):** `atlas-privacy` PyPI package.
* **Phase 12 (Hardening):** Native Docker primitives and standard TLS 1.3.
* **Phase 13 (Consortium Consensus):** **DELETED.** *Upgrade:* We previously planned Raft/Paxos consensus via `etcd`. This is unnecessary distributed complexity. We will use standard **PostgreSQL Logical Replication** (one writer hospital, multi-reader hospitals) until the network exceeds 50 nodes. 

## Phase 14-20: Advanced Trust & Federation
* **Phase 14 (Clinical Pilot):** AWS CloudTrail / ELK for standard HIPAA logging.
* **Phase 15 (Post-Quantum Security):** OpenSSL OQS Fork. Zero custom crypto.
* **Phase 16 (Zero-Knowledge Proving):** **DOWNGRADED TO HARDWARE.** *Upgrade:* Cryptographic ZK-SNARKs (SnarkJS) require massive compute overhead. Since our AAE already blinds the data, we will simply deploy nodes inside **AWS Nitro Enclaves or Intel SGX**. This provides hardware-level attestation that the code wasn't modified, requiring *zero lines of cryptographic code*.
* **Phase 17 (FDA):** CI/CD Git commit hashes act as the traceability matrix.
* **Phase 18 (Federation):** Standard Okta/Keycloak OAuth2.
* **Phase 19 (Hardware Acceleration):** Native PyTorch CUDA bindings.
* **Phase 20 (ADR Finalization):** The architectural constitution: *If an off-the-shelf system call or database can do it, ATLAS will not write custom code for it.*
