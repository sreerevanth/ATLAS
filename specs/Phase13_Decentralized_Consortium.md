# Phase 13: Decentralized Consortium
- **Ledger**: Standard PostgreSQL with logical replication, or managed Hyperledger Fabric if strict trustless environment is required.
- **Consensus**: Standard Raft/Paxos via existing libraries (e.g., etcd).
- **Ponytail note**: Do not build custom blockchains or consensus algorithms.
