import torch
import torch.nn as nn
import torch.optim as optim
import os
from sklearn.datasets import load_breast_cancer
from sklearn.preprocessing import StandardScaler
from atlas.privacy.lpl import LatentEncoder, LatentDecoder, PropertyAdversary
from simulate_real_world import extract_real_topology

def train_lpl():
    print("Extracting Persistence Images from breast cancer dataset...")
    data = load_breast_cancer()
    X = StandardScaler().fit_transform(data.data)
    y = data.target
    
    # We will generate a mini-batch of topologies by taking random subsets
    topologies = []
    labels = []
    
    for _ in range(50):
        # Sample Malignant
        idx = torch.randperm((y==0).sum())[:20]
        pts = X[y==0][idx.numpy()]
        topologies.append(extract_real_topology(pts))
        labels.append(0)
        
        # Sample Benign
        idx = torch.randperm((y==1).sum())[:20]
        pts = X[y==1][idx.numpy()]
        topologies.append(extract_real_topology(pts))
        labels.append(1)
        
    X_train = torch.cat(topologies, dim=0)
    y_train = torch.tensor(labels)
    
    encoder = LatentEncoder(input_dim=2048, latent_dim=128)
    decoder = LatentDecoder(latent_dim=128, output_dim=2048)
    adversary = PropertyAdversary(latent_dim=128, num_classes=2)
    
    opt_enc = optim.Adam(encoder.parameters(), lr=0.001)
    opt_dec = optim.Adam(decoder.parameters(), lr=0.001)
    opt_adv = optim.Adam(adversary.parameters(), lr=0.001)
    
    mse_loss = nn.MSELoss()
    ce_loss = nn.CrossEntropyLoss()
    
    print("Training Adversarial Autoencoder (Latent Privacy Layer)...")
    for epoch in range(1, 21):
        # 1. Train Adversary (Maximize classification accuracy from latent space)
        opt_adv.zero_grad()
        latent = encoder(X_train).detach()
        preds = adversary(latent)
        loss_adv = ce_loss(preds, y_train)
        loss_adv.backward()
        opt_adv.step()
        
        # 2. Train Encoder/Decoder (Minimize MSE + Fool Adversary)
        opt_enc.zero_grad()
        opt_dec.zero_grad()
        
        latent = encoder(X_train)
        reconstructed = decoder(latent)
        
        loss_recon = mse_loss(reconstructed, X_train)
        
        # We want the adversary to fail, so we maximize its cross-entropy (or minimize negative)
        # Weighting the adversarial loss against reconstruction
        adv_preds = adversary(latent)
        loss_fool = -ce_loss(adv_preds, y_train) * 0.1 
        
        loss_total = loss_recon + loss_fool
        loss_total.backward()
        
        opt_enc.step()
        opt_dec.step()
        
        if epoch % 5 == 0:
            print(f"Epoch {epoch}/20 | Recon Loss: {loss_recon.item():.4f} | Adv Loss: {loss_adv.item():.4f}")
            
    os.makedirs("models", exist_ok=True)
    torch.save(encoder.state_dict(), "models/latent_encoder.pt")
    print("Training complete. Weights saved to models/latent_encoder.pt")

if __name__ == "__main__":
    train_lpl()
