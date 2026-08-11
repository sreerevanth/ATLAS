import sys, os
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.random_projection import GaussianRandomProjection

sys.path.insert(0, os.path.abspath('../EXP-002'))
sys.path.insert(1, os.path.abspath('../EXP-001'))
from topology import compute_persistence
from gtda.diagrams import PersistenceImage
from generate_data import get_datasets

def main():
    print("--- EXP-007I: White-Box LSH Attack (1-Bit Compressed Sensing) ---")
    
    # Generate original datasets
    np.random.seed(42)
    datasets = get_datasets(seed=42)
    X_list = list(datasets.values())
    names = list(datasets.keys())
    
    print("Computing Persistence Images...")
    diag = compute_persistence(X_list)
    pi = PersistenceImage(sigma=2.0, n_bins=32) # use smaller bins to make reconstruction easier to measure
    images = pi.fit_transform(diag).reshape(len(diag), -1)
    
    results = []
    
    # We will test different hash lengths to see how reconstruction quality improves
    for n_bits in [32, 64, 128, 256, 512, 1024]:
        # Create White-Box LSH
        projector = GaussianRandomProjection(n_components=n_bits, random_state=42)
        projector.fit(images)
        W = projector.components_ # shape: (n_bits, n_features)
        
        # Attacker intercepts hashes
        hashes = (projector.transform(images) > 0).astype(int)
        
        # 1-Bit Compressed Sensing Reconstruction Attack
        # X_recon = hash_bipolar @ W
        hash_bipolar = np.where(hashes == 1, 1, -1)
        reconstructions = np.dot(hash_bipolar, W)
        
        # Enforce non-negativity (Persistence Images are >= 0)
        reconstructions = np.maximum(reconstructions, 0)
        
        # Calculate Cosine Similarity between original images and reconstructed images
        similarities = []
        for i in range(len(images)):
            sim = cosine_similarity(images[i].reshape(1, -1), reconstructions[i].reshape(1, -1))[0][0]
            similarities.append(sim)
            
        mean_sim = np.mean(similarities)
        print(f"Bits: {n_bits:4d} | Mean Cosine Similarity to Original PI: {mean_sim:.4f}")
        results.append((n_bits, mean_sim))
        
    os.makedirs('results', exist_ok=True)
    with open('results/whitebox_attack.md', 'w', encoding='utf-8') as f:
        f.write("# EXP-007I: White-Box LSH Attack (Image Reconstruction)\n\n")
        f.write("Using 1-Bit Compressed Sensing to reconstruct the raw Persistence Image directly from intercepted hashes and the public projection matrix.\n\n")
        f.write("| Signature Length | Cosine Similarity (Reconstruction Accuracy) |\n")
        f.write("| --- | --- |\n")
        for bits, sim in results:
            f.write(f"| {bits} bits | {sim:.4f} |\n")

if __name__ == '__main__':
    main()
