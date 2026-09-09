import sys, os, time
import numpy as np
from sklearn.metrics import mutual_info_score

sys.path.insert(0, os.path.abspath('../EXP-002'))
sys.path.insert(1, os.path.abspath('../EXP-001'))
from topology import compute_persistence
from hashing import hash_vectors
from gtda.diagrams import PersistenceImage
from sklearn.datasets import make_blobs
from metrics import hash_agreement
from generate_data import get_datasets

def generate_cluster_dataset(n_samples=200, n_classes=5, samples_per_class=50):
    X_list = []
    y_list = []
    np.random.seed(42)
    for i in range(n_classes):
        n_clusters = i + 1
        for j in range(samples_per_class):
            std = np.random.uniform(0.1, 0.5)
            X, _ = make_blobs(n_samples=n_samples, centers=n_clusters, cluster_std=std)
            X_list.append(X)
            y_list.append(n_clusters)
    return X_list, np.array(y_list)

def estimate_mutual_information(hashes, y):
    mi_scores = []
    for i in range(hashes.shape[1]):
        mi_scores.append(mutual_info_score(hashes[:, i], y))
    return np.sum(mi_scores)

def apply_ldp_bit_flip(hashes, flip_prob):
    """
    Applies Local Differential Privacy via Randomized Response.
    Each bit is flipped with probability flip_prob.
    """
    if flip_prob == 0.0:
        return hashes
    mask = np.random.binomial(1, flip_prob, hashes.shape)
    # XOR to flip bits
    return np.logical_xor(hashes, mask).astype(int)

def main():
    print("--- EXP-011B: Local Differential Privacy on LSH Array ---")
    
    # 1. Leakage Dataset
    print("Generating Property Inference Dataset...")
    X_leak, y_leak = generate_cluster_dataset(n_classes=5, samples_per_class=50) 
    diag_leak = compute_persistence(X_leak)
    
    # 2. Retrieval Dataset
    print("Generating Retrieval Dataset...")
    np.random.seed(42)
    X_retrieval_base = list(get_datasets(seed=42).values())
    X_retrieval_noisy = [x + np.random.normal(0, 0.05, x.shape) for x in X_retrieval_base]
    diag_retrieval_base = compute_persistence(X_retrieval_base)
    diag_retrieval_noisy = compute_persistence(X_retrieval_noisy)
    
    print("Computing Baseline Persistence Images...")
    pi = PersistenceImage(sigma=2.0, n_bins=64)
    img_leak = pi.fit_transform(diag_leak).reshape(len(diag_leak), -1)
    img_retrieval_base = pi.fit_transform(diag_retrieval_base).reshape(len(diag_retrieval_base), -1)
    img_retrieval_noisy = pi.fit_transform(diag_retrieval_noisy).reshape(len(diag_retrieval_noisy), -1)
    
    n_bits = 64
    hash_leak_base = hash_vectors(img_leak, n_bits=n_bits)
    hash_ret_base = hash_vectors(img_retrieval_base, n_bits=n_bits)
    hash_ret_noisy = hash_vectors(img_retrieval_noisy, n_bits=n_bits)
    
    results = []
    flip_probs = [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40]
    
    for p in flip_probs:
        np.random.seed(42) # Ensure reproducible DP layer
        
        # Apply LDP to leakage hashes
        hash_leak_ldp = apply_ldp_bit_flip(hash_leak_base, p)
        mi_leak = estimate_mutual_information(hash_leak_ldp, y_leak)
        
        # Apply LDP to retrieval database hashes (simulating server storage)
        hash_ret_base_ldp = apply_ldp_bit_flip(hash_ret_base, p)
        hash_ret_noisy_ldp = apply_ldp_bit_flip(hash_ret_noisy, p)
        
        agreements = []
        for i in range(len(hash_ret_base_ldp)):
            agreements.append(hash_agreement(hash_ret_base_ldp[i], hash_ret_noisy_ldp[i]))
        retrieval_score = np.mean(agreements)
        
        print(f"Flip Prob: {p*100:5.1f}% | Retrieval: {retrieval_score:.2%} | Leakage (MI): {mi_leak:.4f}")
        results.append((p, retrieval_score, mi_leak))

    os.makedirs('results', exist_ok=True)
    with open('results/ldp_layer.md', 'w', encoding='utf-8') as f:
        f.write("# EXP-011B: LDP on Hash Array\n\n")
        f.write("| Bit-Flip Probability | Retrieval | Leakage (MI, nats) |\n")
        f.write("| --- | --- | --- |\n")
        for p, ret, mi in results:
            f.write(f"| {p*100:.1f}% | {ret:.2%} | {mi:.4f} |\n")

if __name__ == '__main__':
    main()
