# SPEC-001: Latent Privacy Layer (LPL) for Topological Signatures

> **Historical material — not current validation evidence.** Retained for design
> context, contributor attribution and provenance. Phase labels, figures and
> capability statements below are not current ATLAS claims. See the
> [current evidence and historical-material guide](../docs/HISTORICAL_MATERIAL.md).

## 1. Objective
To define a cryptographic and mathematically robust privacy layer for the Topology Interchange Protocol (TIP) that mitigates information leakage (property inference) and prevents white-box footprint reconstruction, while preserving high geometric locality for retrieval.

## 2. Motivation
As proven in Phase 9 Empirical Foundations:
* **EXP-007 (Linear Leakage):** Global properties (size, density, clustering) leak linearly into LSH hashes.
* **EXP-011 (DP Failure):** Naive Differential Privacy (Additive Image Noise and Local DP Bit-flipping) catastrophically destroys LSH Hamming retrieval distance before adequately obscuring Mutual Information leakage.
* **EXP-007I (White-Box Vulnerability):** Using 1-bit Compressed Sensing, a white-box attacker possessing the public LSH projection matrix can recover the original Persistence Image footprint from the intercepted hash.

To bypass these vulnerabilities, ATLAS must abandon linear LSH on raw Persistence Images and introduce a non-linear Latent Privacy Layer (LPL).

## 3. Architecture

The LPL operates between the Vectorization (Persistence Image) step and the Hashing (LSH) step.

### 3.1. Component A: The Adversarial Autoencoder (AAE)
A deep neural network composed of three components trained via adversarial minimax game.
1. **Encoder ($E$):** Projects the $32\times32$ Persistence Image ($X$) into a dense latent space $Z$ of dimension 128.
2. **Decoder ($D$):** Attempts to reconstruct $X$ from $Z$. Ensures $Z$ retains geometric utility.
3. **Adversary ($A$):** Takes $Z$ and attempts to predict sensitive global properties (e.g., Cardinality, Density, Domain). 

**Loss Function:**
$$ \mathcal{L}_{Total} = \mathcal{L}_{Reconstruction}(X, D(E(X))) - \lambda \mathcal{L}_{Inference}(Y, A(E(X))) $$
By maximizing the adversary's loss, the Encoder mathematically learns to strip density/cardinality parameters out of $Z$, achieving *Latent Entanglement* where geometry is preserved but macroscopic properties are destroyed.

### 3.2. Component B: Non-Linear Hashing (Latent-LSH)
Instead of a simple Gaussian Random Projection $W$, the LSH function acts upon the hardened latent vector $Z$. 
To prevent 1-bit compressed sensing attacks (EXP-007I), the projection mapping must not be a public, linear matrix. 
* **Mitigation:** The projection matrix $W$ is treated as a Symmetric Cryptographic Key shared only between trusted federated hubs. 
* **Mathematical Bound:** Without $W$, the attacker's best reconstruction strategy relies on brute-forcing a random subspace of dimension $128 \times 64$, which is computationally infeasible.

## 4. Engineering Implementation (ATLAS Runtime)

```python
class LatentPrivacyLayer:
    def __init__(self, encoder_weights_path, lsh_private_key):
        self.encoder = AdversarialEncoder.load(encoder_weights_path)
        self.lsh_projector = PrivateLSH(key=lsh_private_key, n_bits=64)
        
    def generate_signature(self, persistence_image):
        # 1. Non-linear mapping to strip global properties
        z = self.encoder.transform(persistence_image)
        
        # 2. Keyed Projection to prevent 1-bit compressed sensing
        secure_hash = self.lsh_projector.hash(z)
        return secure_hash
```

## 5. Security Guarantees
* **Property Inference:** Bounded by the Adversary's capacity during training. If $\lambda$ is sufficiently high, Mutual Information $I(Z; Y) \to 0$.
* **Reconstruction:** Computationally bounded by the entropy of the symmetric key $W$. 1-bit compressed sensing mathematically fails against non-linear autoencoders without white-box access to the Encoder's parameters.
