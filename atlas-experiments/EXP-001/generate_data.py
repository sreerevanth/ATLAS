import numpy as np
from sklearn.datasets import make_circles, make_blobs, make_swiss_roll

def get_datasets(n_samples=200):
    datasets = {}
    
    # Dataset A: Two circles
    X_circles, _ = make_circles(n_samples=n_samples, factor=0.5, noise=0.0)
    datasets['two_circles'] = X_circles
    
    # Dataset B: Noisy two circles
    X_noisy_circles, _ = make_circles(n_samples=n_samples, factor=0.5, noise=0.1)
    datasets['noisy_circles'] = X_noisy_circles
    
    # Dataset C: Three clusters
    X_clusters, _ = make_blobs(n_samples=n_samples, centers=3, cluster_std=0.5, random_state=42)
    datasets['three_clusters'] = X_clusters
    
    # Dataset D: Swiss roll (projected to 2D)
    X_swiss, _ = make_swiss_roll(n_samples=n_samples, noise=0.0, random_state=42)
    datasets['swiss_roll'] = X_swiss[:, [0, 2]]
    
    # Dataset E: Uniform random
    np.random.seed(42)
    X_random = np.random.uniform(low=-1.0, high=1.0, size=(n_samples, 2))
    datasets['uniform_random'] = X_random
    
    return datasets

def add_noise(X, noise_level=0.01):
    return X + np.random.normal(0, noise_level, X.shape)
