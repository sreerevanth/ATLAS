import numpy as np
from sklearn.random_projection import GaussianRandomProjection

class SimpleLSH:
    def __init__(self, n_bits=16):
        self.n_bits = n_bits
        self.projector = None
        
    def fit(self, X):
        self.projector = GaussianRandomProjection(n_components=self.n_bits, random_state=42)
        self.projector.fit(X)
        
    def transform(self, X):
        projections = self.projector.transform(X)
        return (projections > 0).astype(int)
        
    def fit_transform(self, X):
        self.fit(X)
        return self.transform(X)

def hash_vectors(vectors, n_bits=16):
    lsh = SimpleLSH(n_bits=n_bits)
    return lsh.fit_transform(vectors)
