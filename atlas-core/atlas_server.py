import sqlite3
import hashlib
from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI(title="ATLAS Node API")

API_KEY = "atlas-secret-key"
api_key_header = APIKeyHeader(name="X-API-Key")

def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == API_KEY:
        return api_key_header
    raise HTTPException(status_code=403, detail="Could not validate credentials")

# DB Setup (Standard library, no ORM boilerplate)
def init_db():
    conn = sqlite3.connect("atlas_node.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS topologies 
                 (id INTEGER PRIMARY KEY, node_name TEXT, commitment TEXT, lsh_hash TEXT)''')
    conn.commit()
    conn.close()

init_db()

class TopologyPayload(BaseModel):
    node_name: str
    commitment: str
    lsh_hash: str

@app.post("/publish")
def publish_topology(payload: TopologyPayload, api_key: str = Depends(get_api_key)):
    conn = sqlite3.connect("atlas_node.db")
    c = conn.cursor()
    c.execute("INSERT INTO topologies (node_name, commitment, lsh_hash) VALUES (?, ?, ?)", 
              (payload.node_name, payload.commitment, payload.lsh_hash))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Topology published securely."}

@app.get("/query")
def query_matches(lsh_hash: str, commitment: str, api_key: str = Depends(get_api_key)):
    conn = sqlite3.connect("atlas_node.db")
    c = conn.cursor()
    c.execute("SELECT node_name, commitment, lsh_hash FROM topologies")
    results = c.fetchall()
    conn.close()
    
    matches = []
    for node_name, saved_commitment, saved_hash in results:
        # THE CRYPTOGRAPHIC GATE: Reject immediately if homological properties don't match exactly
        if commitment != saved_commitment:
            continue
            
        hamming_dist = sum(c1 != c2 for c1, c2 in zip(lsh_hash, saved_hash))
        similarity = 1.0 - (hamming_dist / 128.0)
        if similarity > 0.8:
            matches.append({"node": node_name, "similarity": similarity, "hamming": hamming_dist})
            
    return {"matches": matches}

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(api_key: str = ""):
    if api_key != API_KEY:
        return "<h1>401 Unauthorized</h1><p>Please provide ?api_key=...</p>"
        
    conn = sqlite3.connect("atlas_node.db")
    c = conn.cursor()
    c.execute("SELECT id, node_name, commitment, lsh_hash FROM topologies")
    results = c.fetchall()
    conn.close()
    
    html = """
    <html><head><title>ATLAS Dashboard</title>
    <style>body{font-family:sans-serif; background:#1e1e1e; color:#fff; padding:20px;} table{width:100%; border-collapse:collapse;} th,td{padding:10px; border:1px solid #444;}</style>
    </head><body>
    <h1>ATLAS Node Dashboard</h1>
    <table><tr><th>ID</th><th>Node</th><th>Commitment (SHA-256)</th><th>LSH Signature</th></tr>
    """
    for row in results:
        html += f"<tr><td>{row[0]}</td><td>{row[1]}</td><td><code>{row[2][:16]}...</code></td><td><code>{row[3][:32]}...</code></td></tr>"
    html += "</table></body></html>"
    return html

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
