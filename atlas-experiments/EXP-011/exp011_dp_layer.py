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

def apply_dp_mechanism(images, mechanism, param):
    imgs = images.copy()
    if mechanism == 'none':
        return imgs
    elif mechanism == 'noise':
        # Additive Gaussian Noise (Proxy for DP)
        noise = np.random.normal(0, param, imgs.shape)
        return imgs + noise
    elif mechanism == 'dropout':
        # Random Feature Dropout
        mask = np.random.binomial(1, 1 - param, imgs.shape)
        return imgs * mask
    return imgs

def main():
    print("--- EXP-011: Differential Privacy Layer ---")
    
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
    img_leak_base = pi.fit_transform(diag_leak).reshape(len(diag_leak), -1)
    img_retrieval_base = pi.fit_transform(diag_retrieval_base).reshape(len(diag_retrieval_base), -1)
    img_retrieval_noisy = pi.fit_transform(diag_retrieval_noisy).reshape(len(diag_retrieval_noisy), -1)
    
    n_bits = 64
    results = []
    
    # Define DP configurations to test
    configs = [
        ('none', 0.0),
        ('noise', 0.1),
        ('noise', 0.5),
        ('noise', 1.0),
        ('noise', 2.0),
        ('dropout', 0.1),
        ('dropout', 0.3),
        ('dropout', 0.5),
        ('dropout', 0.8)
    ]
    
    for mech, param in configs:
        np.random.seed(42) # Ensure reproducible DP layer
        # Apply DP to leakage images
        dp_img_leak = apply_dp_mechanism(img_leak_base, mech, param)
        hash_leak = hash_vectors(dp_img_leak, n_bits=n_bits)
        mi_leak = estimate_mutual_information(hash_leak, y_leak)
        
        # Apply DP to retrieval images (only the database side needs DP, but we'll apply to both for symmetry)
        # In a real system, the query might also be noised, or just the stored hashes are noised.
        dp_img_retrieval_base = apply_dp_mechanism(img_retrieval_base, mech, param)
        dp_img_retrieval_noisy = apply_dp_mechanism(img_retrieval_noisy, mech, param)
        
        hash_ret_base = hash_vectors(dp_img_retrieval_base, n_bits=n_bits)
        hash_ret_noisy = hash_vectors(dp_img_retrieval_noisy, n_bits=n_bits)
        
        agreements = []
        for i in range(len(hash_ret_base)):
            agreements.append(hash_agreement(hash_ret_base[i], hash_ret_noisy[i]))
        retrieval_score = np.mean(agreements)
        
        name = f"Baseline" if mech == 'none' else f"{mech.capitalize()} ({param})"
        print(f"Mech: {name:15s} | Retrieval: {retrieval_score:.2%} | Leakage (MI): {mi_leak:.4f}")
        results.append((name, retrieval_score, mi_leak))

    os.makedirs('results', exist_ok=True)
    with open('results/dp_layer.md', 'w', encoding='utf-8') as f:
        f.write("# EXP-011: DP Layer Evaluation\n\n")
        f.write("| Mechanism | Parameter | Retrieval | Leakage (MI, nats) |\n")
        f.write("| --- | --- | --- | --- |\n")
        for name, ret, mi in results:
            mech_name = name.split(' ')[0]
            param_val = name.split(' ')[1].strip('()') if '(' in name else 'N/A'
            f.write(f"| {mech_name} | {param_val} | {ret:.2%} | {mi:.4f} |\n")

if __name__ == '__main__':
    main()
