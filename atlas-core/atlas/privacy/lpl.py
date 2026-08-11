import torch
import torch.nn as nn
from typing import Tuple

class LatentEncoder(nn.Module):
    """
    Compresses a Persistence Image into a hardened latent space.
    """
    def __init__(self, input_dim: int = 2048, latent_dim: int = 128):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 512),
            nn.ReLU(),
            nn.Linear(512, latent_dim)
        )
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)

class LatentDecoder(nn.Module):
    """
    Reconstructs the Persistence Image from the latent space to ensure geometric utility.
    """
    def __init__(self, latent_dim: int = 128, output_dim: int = 2048):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(latent_dim, 512),
            nn.ReLU(),
            nn.Linear(512, output_dim),
            nn.ReLU() # Persistence images are non-negative
        )
        
    def forward(self, z: torch.Tensor) -> torch.Tensor:
        return self.net(z)

class PropertyAdversary(nn.Module):
    """
    Attempts to predict sensitive macroscopic properties from the latent space.
    Used exclusively during training to enforce the Latent Privacy Layer constraints.
    """
    def __init__(self, latent_dim: int = 128, num_classes: int = 5):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(latent_dim, 64),
            nn.ReLU(),
            nn.Linear(64, num_classes)
        )
        
    def forward(self, z: torch.Tensor) -> torch.Tensor:
        return self.net(z)

class LatentPrivacyLayer:
    """
    The main interface for the ATLAS Latent Privacy Layer (LPL).
    Takes raw Persistence Images and outputs hardened latent vectors ready for LSH.
    """
    def __init__(self, encoder: LatentEncoder, weights_path: str = "models/latent_encoder.pt"):
        self.encoder = encoder
        import os
        if os.path.exists(weights_path):
            self.encoder.load_state_dict(torch.load(weights_path))
        self.encoder.eval() # Ensure it's in evaluation mode
        
    def transform(self, persistence_images: torch.Tensor) -> torch.Tensor:
        """
        Transforms a batch of Persistence Images into the secure latent space.
        """
        with torch.no_grad():
            return self.encoder(persistence_images)
