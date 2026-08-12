import yaml
import time
import sys
import numpy as np
import os

from generate_data import get_datasets, add_noise
from topology import compute_persistence
import representations
from hashing import hash_vectors
from metrics import hash_agreement, collision_rate

def main():
    print("Loading config...")
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
        
    n_samples = config['experiment']['n_samples']
    noise_level = config['experiment']['noise_level']
    n_bits = config['experiment']['n_bits']
    
    print("Generating datasets...")
    datasets = get_datasets(n_samples)
    dataset_names = list(datasets.keys())
    
    all_point_clouds = []
    noisy_point_clouds = []
    
    for name in dataset_names:
        X = datasets[name]
        all_point_clouds.append(X)
        noisy_point_clouds.append(add_noise(X, noise_level))
        
    combined_pcs = all_point_clouds + noisy_point_clouds
    
    print("Computing persistence diagrams...")
    start_time = time.time()
    diagrams = compute_persistence(combined_pcs)
    topology_time = time.time() - start_time
    
    print("Computing representations...")
    results = {}
    
    n_datasets = len(dataset_names)
    
    rep_methods = [
        ('Landscape', representations.to_landscape),
        ('Image', representations.to_image),
        ('Betti', representations.to_betti),
        ('Entropy', representations.to_entropy)
    ]
    
    for rep_name, get_func in rep_methods:
        start_time = time.time()
        
        # Extract features (flattens if needed)
        reps = get_func(diagrams)
        reps = reps.reshape(len(diagrams), -1)
        
        rep_time = time.time() - start_time
        
        # Hashing
        hashes = hash_vectors(reps, n_bits=n_bits)
        
        mem_size = reps.nbytes
        
        # Stability: Hash agreement between original and noisy
        agreements = []
        for i in range(n_datasets):
            agreements.append(hash_agreement(hashes[i], hashes[i + n_datasets]))
        stability = np.mean(agreements)
        
        # Collision: between different original datasets
        orig_hashes = hashes[:n_datasets]
        coll_rate = collision_rate(orig_hashes)
        
        results[rep_name] = {
            'Stable': f"{stability:.2%}",
            'Collision': f"{coll_rate:.2%}",
            'Runtime': f"{(topology_time + rep_time)/n_datasets:.3f}s",
            'Memory': f"{mem_size/1024:.1f} KB",
            'Hash Agreement': f"{stability:.2f}" 
        }
    
    os.makedirs('results', exist_ok=True)
    report_path = 'report.md'
    
    with open(report_path, 'w') as f:
        f.write("# EXP-001 Results\n\n")
        f.write("| Representation | Stable | Collision | Runtime | Memory | Hash Agreement |\n")
        f.write("| -------------- | ------ | --------- | ------- | ------ | -------------- |\n")
        for rep, _ in rep_methods:
            res = results[rep]
            f.write(f"| {rep} | {res['Stable']} | {res['Collision']} | {res['Runtime']} | {res['Memory']} | {res['Hash Agreement']} |\n")
            
    print(f"Done. Report saved to {report_path}")

if __name__ == '__main__':
    main()
