import sys, os, time
import numpy as np
import itertools

sys.path.insert(0, os.path.abspath('../EXP-002'))
sys.path.insert(1, os.path.abspath('../EXP-001'))
from topology import compute_persistence
from hashing import hash_vectors
from metrics import hash_agreement
from generate_data import get_datasets, add_noise
from gtda.diagrams import PersistenceLandscape, PersistenceImage, BettiCurve, PersistenceEntropy

def main():
    noise = 0.20
    n_seeds = 3
    n_samples = 200
    n_bits = 64
    
    # Grids for sensitivity analysis
    landscape_grid = {
        'n_layers': [1, 3, 5],
        'n_bins': [50, 100, 200, 400]
    }
    
    image_grid = {
        'sigma': [0.1, 0.5, 1.0, 2.0],
        'n_bins': [16, 32, 64] # giotto-tda n_bins translates to pixel resolution
    }
    
    betti_grid = {
        'n_bins': [50, 100, 200, 400]
    }
    
    entropy_grid = {
        'nan_fill_value': [-1] # Minimal params for entropy
    }
    
    def run_grid(name, transformer_class, grid):
        keys = list(grid.keys())
        combinations = list(itertools.product(*[grid[k] for k in keys]))
        
        best_score = -1
        best_params = None
        
        print(f"Sweeping {name} ({len(combinations)} configs)...")
        
        for combo in combinations:
            params = dict(zip(keys, combo))
            # Catch initialization errors for invalid param combos
            try:
                transformer = transformer_class(**params)
            except Exception as e:
                continue
                
            agreements = []
            for seed in range(n_seeds):
                # Generate Data
                base_dict = get_datasets(n_samples, seed=seed)
                base_pcs = list(base_dict.values())
                noisy_pcs = [add_noise(X, noise, seed=seed*100+i) for i, X in enumerate(base_pcs)]
                
                # Compute Topology (this is the expensive part, but we compute it fresh here to be safe)
                base_diag = compute_persistence(base_pcs)
                noisy_diag = compute_persistence(noisy_pcs)
                
                # Convert to Representation
                base_reps = transformer.fit_transform(base_diag).reshape(len(base_diag), -1)
                noisy_reps = transformer.fit_transform(noisy_diag).reshape(len(noisy_diag), -1)
                
                # LSH
                combined = np.vstack([base_reps, noisy_reps])
                hashes = hash_vectors(combined, n_bits=n_bits)
                b_hash = hashes[:len(base_pcs)]
                n_hash = hashes[len(base_pcs):]
                
                # Metrics
                agrs = [hash_agreement(b_hash[i], n_hash[i]) for i in range(len(base_pcs))]
                agreements.append(np.mean(agrs))
                
            score = np.mean(agreements)
            if score > best_score:
                best_score = score
                best_params = params
                
        return best_score, best_params

    results = {}
    results['Landscape'] = run_grid('Landscape', PersistenceLandscape, landscape_grid)
    results['Image'] = run_grid('Image', PersistenceImage, image_grid)
    results['Betti'] = run_grid('Betti', BettiCurve, betti_grid)
    results['Entropy'] = run_grid('Entropy', PersistenceEntropy, entropy_grid)
    
    os.makedirs('results', exist_ok=True)
    report_path = 'results/report.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# EXP-003: Hyperparameter Sensitivity\n\n")
        f.write(f"Tested at challenging noise level {noise*100}% over {n_seeds} seeds.\n\n")
        f.write("| Representation | Best Hash Agreement | Optimized Params |\n")
        f.write("| --- | --- | --- |\n")
        
        for name in ['Landscape', 'Image', 'Betti', 'Entropy']:
            score, params = results[name]
            f.write(f"| {name} | {score:.4f} | `{params}` |\n")
            
    print(f"Sweep complete. Results saved to {report_path}")

if __name__ == '__main__':
    main()
