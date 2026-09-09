import sys, os, time
import numpy as np
from sklearn.metrics import accuracy_score, mutual_info_score
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

sys.path.append(os.path.abspath('../EXP-001'))
sys.path.append(os.path.abspath('../EXP-002'))
from topology import compute_persistence
from hashing import hash_vectors
from gtda.diagrams import PersistenceImage
from sklearn.datasets import make_blobs, make_circles, make_moons

def generate_complex_dataset(n_samples_total=1000):
    X_list = []
    # y contains dict of properties
    properties = {
        'clusters': [],
        'size': [],
        'density': [],
        'domain': [] # 0: Blobs, 1: Circles, 2: Moons
    }
    
    np.random.seed(42)
    for _ in range(n_samples_total):
        domain = np.random.choice([0, 1, 2])
        size = np.random.choice([100, 200, 300, 400, 500])
        density = np.random.choice([0.1, 0.3, 0.5])
        
        if domain == 0:
            clusters = np.random.choice([1, 2, 3, 4, 5])
            X, _ = make_blobs(n_samples=size, centers=clusters, cluster_std=density)
        elif domain == 1:
            clusters = 1 # Not really applicable, set to 1
            noise = density / 2.0
            X, _ = make_circles(n_samples=size, factor=0.5, noise=noise)
        elif domain == 2:
            clusters = 2 # Moons are 2 clusters
            noise = density / 2.0
            X, _ = make_moons(n_samples=size, noise=noise)
            
        X_list.append(X)
        properties['domain'].append(domain)
        properties['size'].append(size)
        properties['density'].append(density)
        properties['clusters'].append(clusters)
        
    for k in properties:
        properties[k] = np.array(properties[k])
        # Convert continuous/float density to categorical string for classification
        if k == 'density':
            properties[k] = properties[k].astype(str)
            
    return X_list, properties

def estimate_mutual_information(hashes, y):
    mi_scores = []
    for i in range(hashes.shape[1]):
        mi_scores.append(mutual_info_score(hashes[:, i], y))
    return np.sum(mi_scores)

def main():
    print("--- EXP-007: Attack Matrix (Property Inference) ---")
    
    print("Generating complex dataset (1000 samples)...")
    X_list, properties = generate_complex_dataset(1000)
    
    print("Computing Persistence Diagrams...")
    diagrams = compute_persistence(X_list)
    
    print("Computing Persistence Images (Optimized Params: sigma=2.0, n_bins=64)...")
    pi = PersistenceImage(sigma=2.0, n_bins=64)
    images = pi.fit_transform(diagrams).reshape(len(diagrams), -1)
    
    n_bits = 64
    print(f"Hashing to {n_bits} bits...")
    hashes = hash_vectors(images, n_bits=n_bits)
    
    results = {}
    
    for prop_name, y in properties.items():
        print(f"\nEvaluating Property: {prop_name.upper()}")
        
        mi = estimate_mutual_information(hashes, y)
        
        X_train, X_test, y_train, y_test = train_test_split(hashes, y, test_size=0.2, random_state=42)
        
        # Baseline (Majority Class)
        unique, counts = np.unique(y_train, return_counts=True)
        majority_class = unique[np.argmax(counts)]
        y_pred_random = np.full_like(y_test, majority_class)
        acc_random = accuracy_score(y_test, y_pred_random)
        
        # A1 Attacker
        lr = LogisticRegression(max_iter=1000)
        lr.fit(X_train, y_train)
        acc_lr = accuracy_score(y_test, lr.predict(X_test))
        
        # A2 Attacker
        rf = RandomForestClassifier(n_estimators=100, random_state=42)
        rf.fit(X_train, y_train)
        acc_rf = accuracy_score(y_test, rf.predict(X_test))
        
        print(f"Mutual Information: {mi:.4f} nats")
        print(f"Random Guess Acc: {acc_random:.2%}")
        print(f"A1 (Logistic Reg): {acc_lr:.2%}")
        print(f"A2 (Random Forest): {acc_rf:.2%}")
        
        results[prop_name] = {
            'MI': mi,
            'Random': acc_random,
            'LR': acc_lr,
            'RF': acc_rf
        }

    os.makedirs('results', exist_ok=True)
    with open('results/attack_matrix.md', 'w', encoding='utf-8') as f:
        f.write("# EXP-007 Attack Matrix (64-bit Hash)\n\n")
        f.write("| Property | Difficulty (Hypothesis) | MI Leakage (nats) | Baseline Acc | A1 (Linear) Acc | A2 (RF) Acc |\n")
        f.write("| --- | --- | --- | --- | --- | --- |\n")
        for prop, res in results.items():
            diff = "Easy" if prop in ['clusters', 'size'] else "Medium" if prop == 'density' else "Hard"
            f.write(f"| **{prop.capitalize()}** | {diff} | {res['MI']:.4f} | {res['Random']:.2%} | {res['LR']:.2%} | {res['RF']:.2%} |\n")

if __name__ == '__main__':
    main()
