import numpy as np
import torch
from typing import Union, List

class KeyedLSH:
    """
    Locality-Sensitive Hashing (LSH) using Gaussian Random Projection.
    This module expects inputs that have already passed through the 
    Latent Privacy Layer (LPL).
    """
    def __init__(self, input_dim: int = 128, signature_size: int = 64, seed: int = 42):
        """
        Initializes the Keyed LSH. 
        Args:
            input_dim: Dimension of the latent vector from LPL (default 128).
            signature_size: Number of bits in the final hash (optimal is 64 per EXP-007).
            seed: Shared cryptographic key/seed across federated nodes.
        """
        self.input_dim = input_dim
        self.signature_size = signature_size
        self.seed = seed
        
        # Initialize the projection matrix deterministically using the shared key
        np.random.seed(self.seed)
        self.projection_matrix = np.random.randn(self.input_dim, self.signature_size)
        
    def hash_vector(self, vector: Union[np.ndarray, torch.Tensor]) -> str:
        """
        Hashes a single vector into a binary signature string.
        """
        if isinstance(vector, torch.Tensor):
            vector = vector.detach().cpu().numpy()
            
        vector = vector.flatten()
        if vector.shape[0] != self.input_dim:
            raise ValueError(f"Expected input dimension {self.input_dim}, got {vector.shape[0]}")
            
        # Random projection
        projection = np.dot(vector, self.projection_matrix)
        
        # Binarize
        binary_hash = (projection > 0).astype(int)
        
        # Convert to string for easy transmission
        return "".join(map(str, binary_hash))
        
    def hash_batch(self, vectors: Union[np.ndarray, torch.Tensor]) -> List[str]:
        """
        Hashes a batch of vectors.
        """
        if isinstance(vectors, torch.Tensor):
            vectors = vectors.detach().cpu().numpy()
            
        projections = np.dot(vectors, self.projection_matrix)
        binary_hashes = (projections > 0).astype(int)
        
        return ["".join(map(str, h)) for h in binary_hashes]
