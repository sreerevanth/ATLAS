import sys, os, time
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

sys.path.append(os.path.abspath('../EXP-001'))
sys.path.append(os.path.abspath('../EXP-002'))
from topology import compute_persistence
from hashing import hash_vectors
from gtda.diagrams import PersistenceImage
from sklearn.datasets import make_blobs

def generate_cluster_dataset(n_samples=200, n_classes=5, samples_per_class=100):
    """Generates point clouds with varying number of clusters (1 to n_classes)."""
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

def main():
    print("Generating dataset for EXP-007 (Property Inference: Number of Clusters)...")
    n_classes = 5
    X_list, y = generate_cluster_dataset(n_samples=200, n_classes=n_classes, samples_per_class=100)
    
    print("Computing Persistence Diagrams...")
    diagrams = compute_persistence(X_list)
    
    print("Computing Persistence Images (Optimized Params: sigma=2.0, n_bins=64)...")
    pi = PersistenceImage(sigma=2.0, n_bins=64)
    images = pi.fit_transform(diagrams).reshape(len(diagrams), -1)
    
    results = {}
    bits_to_test = [32, 64, 128, 256]
    
    for n_bits in bits_to_test:
        print(f"\n--- Testing {n_bits}-bit Hash ---")
        hashes = hash_vectors(images, n_bits=n_bits)
        
        X_train, X_test, y_train, y_test = train_test_split(hashes, y, test_size=0.2, random_state=42)
        
        # Baseline: Random Guess (Majority Class)
        majority_class = np.argmax(np.bincount(y_train))
        y_pred_random = np.full_like(y_test, majority_class)
        acc_random = accuracy_score(y_test, y_pred_random)
        
        # A1 Weak Attacker: Logistic Regression
        lr = LogisticRegression(max_iter=1000)
        lr.fit(X_train, y_train)
        acc_lr = accuracy_score(y_test, lr.predict(X_test))
        
        # A2 Stronger Attacker: Random Forest
        rf = RandomForestClassifier(n_estimators=100, random_state=42)
        rf.fit(X_train, y_train)
        acc_rf = accuracy_score(y_test, rf.predict(X_test))
        
        print(f"Random Guess Acc: {acc_random:.2%}")
        print(f"Logistic Regression Acc: {acc_lr:.2%}")
        print(f"Random Forest Acc: {acc_rf:.2%}")
        
        results[n_bits] = {
            'Random': acc_random,
            'LR': acc_lr,
            'RF': acc_rf
        }

    os.makedirs('results', exist_ok=True)
    report_path = 'results/report.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# EXP-007C & EXP-007G: Property Inference & Signature Length\n\n")
        f.write("Task: Predict the number of clusters (1 to 5) from the LSH hash.\n\n")
        f.write("| Bits | Random Guess | Logistic Regression | Random Forest |\n")
        f.write("| --- | --- | --- | --- |\n")
        for bits in bits_to_test:
            res = results[bits]
            f.write(f"| {bits} | {res['Random']:.2%} | {res['LR']:.2%} | {res['RF']:.2%} |\n")
            
    print(f"\nDone. Saved to {report_path}")

if __name__ == '__main__':
    main()
