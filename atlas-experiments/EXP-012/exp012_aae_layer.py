import os
import sys
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.model_selection import train_test_split
from sklearn.metrics import mutual_info_score

sys.path.insert(0, os.path.abspath('../EXP-002'))
sys.path.insert(1, os.path.abspath('../EXP-001'))
from topology import compute_persistence
from gtda.diagrams import PersistenceImage
from generate_data import get_datasets
from sklearn.datasets import make_blobs

# --- 1. Dataset Generation ---
def generate_aae_dataset(n_samples=500, n_classes=5, samples_per_class=100):
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

# --- 2. PyTorch AAE Models ---
class Encoder(nn.Module):
    def __init__(self, input_dim=2048, latent_dim=128):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 512),
            nn.ReLU(),
            nn.Linear(512, latent_dim)
        )
    def forward(self, x):
        return self.net(x)

class Decoder(nn.Module):
    def __init__(self, latent_dim=128, output_dim=2048):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(latent_dim, 512),
            nn.ReLU(),
            nn.Linear(512, output_dim),
            nn.ReLU() # Persistence images are non-negative
        )
    def forward(self, z):
        return self.net(z)

class Adversary(nn.Module):
    def __init__(self, latent_dim=128, num_classes=5):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(latent_dim, 64),
            nn.ReLU(),
            nn.Linear(64, num_classes)
        )
    def forward(self, z):
        return self.net(z)

def main():
    print("--- EXP-012: Adversarial Autoencoder (Latent Privacy Layer) ---")
    
    # Generate and Vectorize Data
    print("Generating training data...")
    X_raw, y_labels = generate_aae_dataset()
    diag = compute_persistence(X_raw)
    
    pi = PersistenceImage(sigma=2.0, n_bins=32)
    images = pi.fit_transform(diag).reshape(len(diag), -1)
    
    # Map labels 1-5 to 0-4 for PyTorch CrossEntropy
    y_labels = y_labels - 1 
    
    X_train, X_test, y_train, y_test = train_test_split(images, y_labels, test_size=0.2, random_state=42)
    
    X_train_t = torch.FloatTensor(X_train)
    y_train_t = torch.LongTensor(y_train)
    X_test_t = torch.FloatTensor(X_test)
    y_test_t = torch.LongTensor(y_test)
    
    # Initialize models
    enc = Encoder(input_dim=2048, latent_dim=128)
    dec = Decoder(latent_dim=128, output_dim=2048)
    adv = Adversary(latent_dim=128, num_classes=5)
    
    optimizer_G = optim.Adam(list(enc.parameters()) + list(dec.parameters()), lr=1e-3)
    optimizer_A = optim.Adam(adv.parameters(), lr=1e-3)
    
    mse_loss = nn.MSELoss()
    ce_loss = nn.CrossEntropyLoss()
    
    epochs = 100
    lambda_adv = 0.5 # Adversarial penalty weight
    
    print("Training Adversarial Autoencoder...")
    for epoch in range(epochs):
        # 1. Train Adversary
        optimizer_A.zero_grad()
        z = enc(X_train_t).detach() # Don't update encoder here
        preds = adv(z)
        loss_A = ce_loss(preds, y_train_t)
        loss_A.backward()
        optimizer_A.step()
        
        # 2. Train Autoencoder (Encoder + Decoder)
        optimizer_G.zero_grad()
        z = enc(X_train_t)
        recon = dec(z)
        preds = adv(z)
        
        # We want to MINIMIZE reconstruction error, but MAXIMIZE adversary error
        # (By minimizing negative cross-entropy or maximizing cross entropy)
        loss_recon = mse_loss(recon, X_train_t)
        loss_adv = ce_loss(preds, y_train_t) 
        
        loss_G = loss_recon - (lambda_adv * loss_adv) 
        loss_G.backward()
        optimizer_G.step()
        
        if (epoch+1) % 20 == 0:
            print(f"Epoch {epoch+1}/{epochs} | Recon Loss: {loss_recon.item():.4f} | Adv Loss: {loss_A.item():.4f}")
            
    # Evaluation
    print("\nEvaluating Latent Privacy Layer...")
    enc.eval()
    adv.eval()
    with torch.no_grad():
        z_test = enc(X_test_t)
        preds_test = adv(z_test).argmax(dim=1)
        acc = (preds_test == y_test_t).float().mean().item()
        
        # Estimate MI in latent space (discretized for simplicity)
        mi_scores = []
        z_np = z_test.numpy()
        for i in range(z_np.shape[1]):
            # Binarize latent space at mean 0 for MI estimation
            mi_scores.append(mutual_info_score(z_np[:, i] > 0, y_test))
        mi_sum = np.sum(mi_scores)
        
    print(f"Adversary Prediction Accuracy on Z: {acc*100:.2f}% (Random guess = 20%)")
    print(f"Mutual Information Leakage in Latent Space: {mi_sum:.4f}")

if __name__ == '__main__':
    main()
