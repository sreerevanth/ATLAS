import os
import torch
import numpy as np
import pytest
from fastapi.testclient import TestClient
import sqlite3

from simulate_real_world import extract_real_topology, TopologyCommitment, RandomProjectionLSH
from atlas_server import app, init_db

# Pytest fixture for FastAPI test client
@pytest.fixture
def client():
    # Setup test DB
    if os.path.exists("atlas_node.db"):
        os.remove("atlas_node.db")
    init_db()
    
    with TestClient(app) as c:
        yield c

def test_tda_mathematics():
    """Test mathematically known topology extraction"""
    from sklearn.datasets import load_breast_cancer
    from sklearn.preprocessing import StandardScaler
    
    data = load_breast_cancer()
    X = StandardScaler().fit_transform(data.data)
    
    # Take a dense cluster that will definitely generate H1 loops
    subset = X[:100]
    pi_cluster = extract_real_topology(subset)
    
    assert pi_cluster.shape == (1, 2048)
    assert torch.sum(pi_cluster).item() > 0.0
    
    # 2. Simple scattered points (Likely no H1 components, handled by our zero-pad fix)
    np.random.seed(42)
    noise = np.random.randn(5, 2)
    pi_noise = extract_real_topology(noise)
    assert pi_noise.shape == (1, 2048)

def test_cryptographic_commitment():
    """Test that the commitment correctly handles exact matches and rejects variations"""
    vec1 = torch.ones((1, 2048))
    vec2 = torch.ones((1, 2048))
    vec3 = torch.zeros((1, 2048))
    
    c1 = TopologyCommitment.generate_commitment(vec1)
    
    # Exact same vector should verify
    assert TopologyCommitment.verify_commitment(c1, vec2) is True
    
    # Different vector should fail
    assert TopologyCommitment.verify_commitment(c1, vec3) is False

def test_lsh_hashing():
    """Test standard Random Projection LSH is deterministic"""
    lsh = RandomProjectionLSH(input_dim=128, signature_size=128, seed=42)
    vec = torch.randn(1, 128)
    
    hash1 = lsh.hash_vector(vec)
    hash2 = lsh.hash_vector(vec)
    
    assert type(hash1) == str
    assert len(hash1) == 128
    assert hash1 == hash2 # Determinism

def test_api_authentication(client):
    """Test the API Key authentication logic"""
    # Missing auth (FastAPI returns 403 by default for APIKeyHeader without auto_error=False, wait actually 403)
    resp = client.post("/publish", json={"node_name": "Test", "commitment": "c", "lsh_hash": "h"})
    assert resp.status_code in (401, 403)
    
    # Wrong auth
    resp = client.post("/publish", json={"node_name": "Test", "commitment": "c", "lsh_hash": "h"}, headers={"X-API-Key": "wrong"})
    assert resp.status_code in (401, 403)
    
    # Correct auth
    resp = client.post("/publish", json={"node_name": "Test", "commitment": "c", "lsh_hash": "h"}, headers={"X-API-Key": "atlas-secret-key"})
    assert resp.status_code == 200

def test_api_commitment_gate(client):
    """Test that the API correctly enforces the Cryptographic Commitment"""
    headers = {"X-API-Key": "atlas-secret-key"}
    # Publish Node A
    client.post("/publish", json={"node_name": "Node A", "commitment": "COMMIT_A", "lsh_hash": "0"*128}, headers=headers)
    
    # Query with matching commitment
    resp1 = client.get("/query?lsh_hash=" + "0"*128 + "&commitment=COMMIT_A", headers=headers)
    assert resp1.status_code == 200
    assert len(resp1.json()["matches"]) == 1
    assert resp1.json()["matches"][0]["node"] == "Node A"
    
    # Query with wrong commitment (The Gate)
    resp2 = client.get("/query?lsh_hash=" + "0"*128 + "&commitment=COMMIT_B", headers=headers)
    assert resp2.status_code == 200
    assert len(resp2.json()["matches"]) == 0 # Rejected by gate

def test_sqlite_persistence(client):
    """Test that data survives database connection restarts"""
    headers = {"X-API-Key": "atlas-secret-key"}
    client.post("/publish", json={"node_name": "PersistentNode", "commitment": "123", "lsh_hash": "abc"}, headers=headers)
    
    # Check directly from DB outside of API
    conn = sqlite3.connect("atlas_node.db")
    c = conn.cursor()
    c.execute("SELECT node_name FROM topologies WHERE commitment='123'")
    res = c.fetchone()
    conn.close()
    
    assert res is not None
    assert res[0] == "PersistentNode"
