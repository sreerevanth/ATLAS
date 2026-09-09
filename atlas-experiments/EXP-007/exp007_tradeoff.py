import sys, os, time
import numpy as np
from sklearn.metrics import accuracy_score, mutual_info_score
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression

sys.path.insert(0, os.path.abspath('../EXP-002'))
sys.path.insert(1, os.path.abspath('../EXP-001'))
from topology import compute_persistence
from hashing import hash_vectors
from gtda.diagrams import PersistenceImage
from sklearn.datasets import make_blobs
from metrics import hash_agreement
from generate_data import get_datasets

def generate_cluster_dataset(n_samples=200, n_classes=5, samples_per_class=100):
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
    # To estimate MI between a binary hash string and a categorical target 'y'
    # we can treat each bit as a feature, or compute MI on the exact hash string.
    # Because hash space is huge, we'll compute the average MI between each bit and y.
    # A more rigorous approach is evaluating the classifier accuracy / cross-entropy.
    # We will use Logistic Regression cross entropy as a proxy, but let's just calculate
    # the average MI of the bits with the target to show the trend.
    mi_scores = []
    for i in range(hashes.shape[1]):
        mi_scores.append(mutual_info_score(hashes[:, i], y))
    return np.sum(mi_scores) # Total bits of information leaked across all hash bits (naive sum)

def main():
    print("--- EXP-007: Privacy vs Retrieval Trade-off ---")
    
    # 1. Leakage Dataset
    print("Generating Property Inference Dataset...")
    X_leak, y_leak = generate_cluster_dataset(n_classes=5, samples_per_class=50) # smaller for speed
    diag_leak = compute_persistence(X_leak)
    
    # 2. Retrieval Dataset
    print("Generating Retrieval Dataset (EXP-002 style)...")
    np.random.seed(42)
    X_retrieval_base = list(get_datasets(seed=42).values())
    # add noise
    X_retrieval_noisy = [x + np.random.normal(0, 0.05, x.shape) for x in X_retrieval_base]
    diag_retrieval_base = compute_persistence(X_retrieval_base)
    diag_retrieval_noisy = compute_persistence(X_retrieval_noisy)
    
    print("Computing Persistence Images...")
    pi = PersistenceImage(sigma=2.0, n_bins=64)
    
    img_leak = pi.fit_transform(diag_leak).reshape(len(diag_leak), -1)
    img_retrieval_base = pi.fit_transform(diag_retrieval_base).reshape(len(diag_retrieval_base), -1)
    img_retrieval_noisy = pi.fit_transform(diag_retrieval_noisy).reshape(len(diag_retrieval_noisy), -1)
    
    bits_to_test = [32, 64, 128, 256, 512]
    results = {}
    
    for n_bits in bits_to_test:
        # Leakage
        hash_leak = hash_vectors(img_leak, n_bits=n_bits)
        mi_leak = estimate_mutual_information(hash_leak, y_leak)
        
        # Attack Accuracy (A1)
        X_train, X_test, y_train, y_test = train_test_split(hash_leak, y_leak, test_size=0.2, random_state=42)
        lr = LogisticRegression(max_iter=1000)
        lr.fit(X_train, y_train)
        acc_leak = accuracy_score(y_test, lr.predict(X_test))
        
        # Retrieval
        hash_ret_base = hash_vectors(img_retrieval_base, n_bits=n_bits)
        hash_ret_noisy = hash_vectors(img_retrieval_noisy, n_bits=n_bits)
        
        # Hash agreement (how many bits match on average between base and noisy)
        # metrics.hash_agreement expects 0/1 vectors
        agreements = []
        for i in range(len(hash_ret_base)):
            agreements.append(hash_agreement(hash_ret_base[i], hash_ret_noisy[i]))
        retrieval_score = np.mean(agreements)
        
        print(f"Bits: {n_bits:3d} | Retrieval: {retrieval_score:.2%} | Leakage (MI): {mi_leak:.4f} | A1 Acc: {acc_leak:.2%}")
        results[n_bits] = {'Retrieval': retrieval_score, 'MI': mi_leak, 'Acc': acc_leak}

    os.makedirs('results', exist_ok=True)
    with open('results/tradeoff.md', 'w', encoding='utf-8') as f:
        f.write("# The Privacy-Retrieval Trade-off\n\n")
        f.write("| Signature Length (b) | Retrieval(b) | Leakage(b) [Sum MI] | A1 Accuracy |\n")
        f.write("| --- | --- | --- | --- |\n")
        for bits in bits_to_test:
            res = results[bits]
            f.write(f"| {bits} bits | {res['Retrieval']:.2%} | {res['MI']:.4f} nats | {res['Acc']:.2%} |\n")

if __name__ == '__main__':
    main()
