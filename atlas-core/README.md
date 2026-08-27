# ATLAS Privacy SDK

The `atlas-privacy` SDK is the core implementation of the ATLAS Master Plan, providing developers with the mathematical tools to perform **Privacy-Preserving Federated Topological Dataset Matching**. 

With this SDK, you can compute topological features (Betti numbers), filter them through an Adversarial Autoencoder (AAE), and generate Locality-Sensitive Hashes (LSH) that map dataset geometry without leaking raw patient or client data.

## Installation

Install the package directly via pip. Ensure you are using Python 3.9+:

```bash
pip install atlas-privacy
```

*(Note: If building from source, navigate to this directory and run `pip install .`)*

## Core Modules

The SDK exposes several core capabilities natively:

### 1. Topology Computation
Compute exact Vietoris-Rips complexes and persistence images from raw coordinate data.
```python
from atlas.topology import compute_persistence
```

### 2. Latent Privacy Layer (AAE)
Scrub structural Mutual Information (MI) using the trained Adversarial Autoencoder.
```python
from atlas.privacy.lpl import LatentPrivacyLayer

# Initialize the layer (loads weights automatically if available)
privacy_layer = LatentPrivacyLayer(input_dim=100, latent_dim=16)
```

### 3. Cryptographic Hashing
Generate Gaussian random projections (LSH) and secure SHA-256 commitments for topology verification.
```python
from atlas.hashing.lsh import RandomProjectionLSH
from atlas.protocol.message import TopologyCommitment

hasher = RandomProjectionLSH(input_dim=16, num_bits=256)
```

## Running the Node Server

The SDK includes a built-in FastAPI implementation that you can launch immediately. This server handles incoming `/publish` and `/query` HTTP requests natively and stores state in a local SQLite database (`atlas_node.db`).

```bash
# Launch the Atlas server node on port 8000
python -m uvicorn atlas_server:app --host 0.0.0.0 --port 8000
```

Once running, you can access the live dashboard at:
`http://localhost:8000/dashboard`

## Security Warning

This is currently a **Research Prototype (v0.1.0)**. 
- API keys are statically defined.
- Cryptographic commitments use SHA-256 (Not yet Zero-Knowledge).
- LSH hashing uses Random Projections (Not yet Post-Quantum LWE).

Do not deploy this in a production medical environment without implementing the Phase 12-15 hardening roadmap.
