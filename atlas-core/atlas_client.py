import torch
import requests
import numpy as np
import logging
from sklearn.datasets import load_breast_cancer
from sklearn.preprocessing import StandardScaler
from atlas.privacy.lpl import LatentEncoder, LatentPrivacyLayer
from simulate_real_world import extract_real_topology, TopologyCommitment, RandomProjectionLSH

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("AtlasClient")

# Configuration
SERVER_URL = "http://localhost:8000"
API_KEY = "atlas-secret-key"
HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

def run_real_client():
    logger.info("Initializing ATLAS HTTP Client.")
    
    data = load_breast_cancer()
    X = StandardScaler().fit_transform(data.data)
    y = data.target
    
    X_malignant = X[y == 0]
    X_benign = X[y == 1]
    
    X_mal_A = X_malignant[:len(X_malignant)//2]
    X_mal_B = X_malignant[len(X_malignant)//2:]
    
    encoder = LatentEncoder(input_dim=2048, latent_dim=128)
    lpl = LatentPrivacyLayer(encoder)
    shared_lsh = RandomProjectionLSH(input_dim=128, signature_size=128, seed=888)
    
    # -------------------------------------------------------------
    # NODE A: Publishing Data
    # -------------------------------------------------------------
    logger.info("Node A: Extracting topology.")
    pi_a = extract_real_topology(X_mal_A)
    
    commitment_a = TopologyCommitment.generate_commitment(pi_a)
    hash_a = shared_lsh.hash_vector(lpl.transform(pi_a))
    
    logger.info("Node A: Publishing to network.")
    payload = {
        "node_name": "Node A",
        "commitment": commitment_a,
        "lsh_hash": hash_a
    }
    resp = requests.post(f"{SERVER_URL}/publish", json=payload, headers=HEADERS)
    logger.info(f"Node A Publish Response: {resp.status_code}")
    
    # -------------------------------------------------------------
    # ADVERSARY: Probing with Benign
    # -------------------------------------------------------------
    logger.info("Adversary: Probing network with Benign dataset.")
    pi_adv = extract_real_topology(X_benign)
    commitment_adv = TopologyCommitment.generate_commitment(pi_adv)
    hash_adv = shared_lsh.hash_vector(lpl.transform(pi_adv))
    
    resp = requests.get(f"{SERVER_URL}/query", params={"lsh_hash": hash_adv, "commitment": commitment_adv}, headers=HEADERS)
    matches = resp.json().get("matches", [])
    if not matches:
        logger.info("Adversary: Query rejected or no matches found (Expected).")
    else:
        logger.error("Adversary: Found matches! (Vulnerability)")

    # -------------------------------------------------------------
    # NODE B: Collaborative Match
    # -------------------------------------------------------------
    logger.info("Node B: Extracting Topology.")
    pi_b = extract_real_topology(X_mal_B)
    
    commitment_b = TopologyCommitment.generate_commitment(pi_b)
    hash_b = shared_lsh.hash_vector(lpl.transform(pi_b))
    
    logger.info("Node B: Querying network.")
    resp = requests.get(f"{SERVER_URL}/query", params={"lsh_hash": hash_b, "commitment": commitment_a}, headers=HEADERS)
    matches = resp.json().get("matches", [])
    
    if matches:
        logger.info(f"Node B: Match found. {matches}")
    else:
        logger.warning("Node B: No match found.")

if __name__ == "__main__":
    run_real_client()
