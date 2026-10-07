# Phase 13: Decentralized Consortium

> **Historical material — not current validation evidence.** Retained for design
> context, contributor attribution and provenance. Phase labels, figures and
> capability statements below are not current ATLAS claims. See the
> [current evidence and historical-material guide](../docs/HISTORICAL_MATERIAL.md).
- **Ledger**: Standard PostgreSQL with logical replication, or managed Hyperledger Fabric if strict trustless environment is required.
- **Consensus**: Standard Raft/Paxos via existing libraries (e.g., etcd).
- **Ponytail note**: Do not build custom blockchains or consensus algorithms.
