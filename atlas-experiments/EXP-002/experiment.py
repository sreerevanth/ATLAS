import sys, os, time
import numpy as np

sys.path.append(os.path.abspath('../EXP-001'))
from topology import compute_persistence
import representations
from hashing import hash_vectors
from metrics import hash_agreement

from generate_data import get_datasets, add_noise

def main():
    noise_levels = [0.0, 0.01, 0.02, 0.05, 0.10, 0.20, 0.30, 0.50]
    n_seeds = 10 # 10 independent runs for statistical significance
    n_samples = 200
    n_bits = 64
    
    rep_methods = [
        ('Landscape', representations.to_landscape),
        ('Image', representations.to_image),
        ('Betti', representations.to_betti),
        ('Entropy', representations.to_entropy)
    ]
    
    # Store stability results: {rep: {noise: [stabilities...]}}
    stability_results = {rep: {noise: [] for noise in noise_levels} for rep, _ in rep_methods}
    
    print(f"Starting EXP-002: Noise Robustness Sweep ({n_seeds} seeds)")
    
    for seed in range(n_seeds):
        print(f"  Run {seed+1}/{n_seeds}...")
        
        # 1. Base datasets (0 noise)
        base_datasets_dict = get_datasets(n_samples, seed=seed)
        dataset_names = list(base_datasets_dict.keys())
        base_pcs = [base_datasets_dict[name] for name in dataset_names]
        
        # 2. Compute Base Topologies
        base_diagrams = compute_persistence(base_pcs)
        
        # 3. Base Representations & Hashes
        base_reps_dict = {}
        base_hashes_dict = {}
        for rep_name, get_func in rep_methods:
            reps = get_func(base_diagrams).reshape(len(base_diagrams), -1)
            base_reps_dict[rep_name] = reps
            base_hashes_dict[rep_name] = hash_vectors(reps, n_bits=n_bits)
            
        # 4. Sweep Noise
        for noise in noise_levels:
            if noise == 0.0:
                for rep_name, _ in rep_methods:
                    stability_results[rep_name][noise].append(1.0)
                continue
                
            # Add noise to base datasets
            noisy_pcs = [add_noise(X, noise, seed=seed*100+i) for i, X in enumerate(base_pcs)]
            noisy_diagrams = compute_persistence(noisy_pcs)
            
            for rep_name, get_func in rep_methods:
                noisy_reps = get_func(noisy_diagrams).reshape(len(noisy_diagrams), -1)
                
                # To test hash stability properly, we should use the SAME hash projection as the base
                # However, for simplicity here, we re-hash both together to ensure they use the same projection matrix
                # A robust system fits LSH on historical data. Here we fit on base + noisy.
                combined_reps = np.vstack([base_reps_dict[rep_name], noisy_reps])
                combined_hashes = hash_vectors(combined_reps, n_bits=n_bits)
                
                b_hashes = combined_hashes[:len(base_pcs)]
                n_hashes = combined_hashes[len(base_pcs):]
                
                # Calculate agreement for this noise level
                agreements = [hash_agreement(b_hashes[i], n_hashes[i]) for i in range(len(base_pcs))]
                stability = np.mean(agreements)
                stability_results[rep_name][noise].append(stability)
                
    # 5. Summarize Results
    os.makedirs('results', exist_ok=True)
    report_path = 'results/report.md'
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# EXP-002: Noise Robustness Results\n\n")
        f.write("Averaged over 10 random seeds.\n\n")
        
        # Table Header
        headers = ["Representation"] + [f"σ={int(n*100)}%" for n in noise_levels]
        f.write("| " + " | ".join(headers) + " |\n")
        f.write("| " + " | ".join(["---"] * len(headers)) + " |\n")
        
        for rep_name, _ in rep_methods:
            row = [rep_name]
            for noise in noise_levels:
                mean_stab = np.mean(stability_results[rep_name][noise])
                std_stab = np.std(stability_results[rep_name][noise])
                row.append(f"{mean_stab:.2f} (±{std_stab:.2f})")
            f.write("| " + " | ".join(row) + " |\n")
            
    print(f"Sweep complete. Results saved to {report_path}")

if __name__ == '__main__':
    main()
