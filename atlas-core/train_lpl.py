import torch
import torch.nn as nn
import torch.optim as optim
import os
import math
from sklearn.datasets import load_breast_cancer
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from atlas.privacy.lpl import LatentEncoder, LatentDecoder, PropertyAdversary
from simulate_real_world import extract_real_topology

def generate_topology_dataset(X, y, samples_per_class=150):
    print(f"Generating Topological Persistence Images for {samples_per_class*2} samples...")
    topologies = []
    labels = []
    
    for _ in range(samples_per_class):
        # Sample Malignant (0)
        idx = torch.randperm((y==0).sum())[:20]
        pts = X[y==0][idx.numpy()]
        topologies.append(extract_real_topology(pts))
        labels.append(0)
        
        # Sample Benign (1)
        idx = torch.randperm((y==1).sum())[:20]
        pts = X[y==1][idx.numpy()]
        topologies.append(extract_real_topology(pts))
        labels.append(1)
        
    X_tensor = torch.cat(topologies, dim=0)
    y_tensor = torch.tensor(labels)
    return X_tensor, y_tensor

def train_lpl():
    data = load_breast_cancer()
    X = StandardScaler().fit_transform(data.data)
    y = data.target
    
    X_all, y_all = generate_topology_dataset(X, y, samples_per_class=200)
    
    # 80/20 Train/Validation Split
    X_train, X_val, y_train, y_val = train_test_split(X_all, y_all, test_size=0.2, random_state=42)
    
    encoder = LatentEncoder(input_dim=2048, latent_dim=128)
    decoder = LatentDecoder(latent_dim=128, output_dim=2048)
    adversary = PropertyAdversary(latent_dim=128, num_classes=2)
    
    opt_enc = optim.AdamW(encoder.parameters(), lr=0.002, weight_decay=1e-4)
    opt_dec = optim.AdamW(decoder.parameters(), lr=0.002, weight_decay=1e-4)
    opt_adv = optim.AdamW(adversary.parameters(), lr=0.005, weight_decay=1e-4)
    
    scheduler_enc = optim.lr_scheduler.ReduceLROnPlateau(opt_enc, mode='min', factor=0.5, patience=10)
    scheduler_dec = optim.lr_scheduler.ReduceLROnPlateau(opt_dec, mode='min', factor=0.5, patience=10)
    
    mse_loss = nn.MSELoss()
    ce_loss = nn.CrossEntropyLoss()
    
    print("Training Adversarial Autoencoder (Latent Privacy Layer) with rigorous validation...")
    
    epochs = 200
    alpha = 0.5 # Adversarial penalty weight
    
    best_val_loss = float('inf')
    
    for epoch in range(1, epochs + 1):
        # --- TRAINING PHASE ---
        encoder.train()
        decoder.train()
        adversary.train()
        
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
        
        adv_preds = adversary(latent)
        # We want the adversary's predictions to be uniform (maximum entropy), so we penalize it
        loss_fool = -ce_loss(adv_preds, y_train) * alpha 
        
        loss_total = loss_recon + loss_fool
        loss_total.backward()
        
        # Gradient clipping for stability
        torch.nn.utils.clip_grad_norm_(encoder.parameters(), max_norm=1.0)
        torch.nn.utils.clip_grad_norm_(decoder.parameters(), max_norm=1.0)
        
        opt_enc.step()
        opt_dec.step()
        
        # --- VALIDATION PHASE ---
        encoder.eval()
        decoder.eval()
        adversary.eval()
        with torch.no_grad():
            val_latent = encoder(X_val)
            val_reconstructed = decoder(val_latent)
            val_recon_loss = mse_loss(val_reconstructed, X_val)
            
            val_adv_preds = adversary(val_latent)
            val_adv_loss = ce_loss(val_adv_preds, y_val)
            
            val_adv_acc = (torch.argmax(val_adv_preds, dim=1) == y_val).float().mean()
            
        scheduler_enc.step(val_recon_loss)
        scheduler_dec.step(val_recon_loss)
        
        if val_recon_loss < best_val_loss:
            best_val_loss = val_recon_loss
            os.makedirs("models", exist_ok=True)
            torch.save(encoder.state_dict(), "models/latent_encoder.pt")
            
        if epoch % 20 == 0:
            print(f"Epoch {epoch:03d}/{epochs} | Train Recon: {loss_recon.item():.4f} | Val Recon: {val_recon_loss.item():.4f} | Val Adv Acc: {val_adv_acc.item():.4f} (Target ~0.50)")
            
    print(f"Training fully validated. Best Val Recon Loss: {best_val_loss:.4f}")
    print("Optimal Weights saved to models/latent_encoder.pt")

if __name__ == "__main__":
    train_lpl()
