import base64
import json

import numpy as np
import pytest
import wasmtime
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from atlas.protocol import LocalNode, envelope, local_signature, open_envelope
from atlas.sandbox import count_module, execute


def test_signed_execution_and_fuel_and_memory():
    signer = Ed25519PrivateKey.generate()
    public = signer.public_key().public_bytes_raw()
    module = count_module()
    region = b'\x01\x02\x03'
    assert execute(module, signer.sign(module), public, region) == b'\x06\x00\x00\x00'
    with pytest.raises(InvalidSignature):
        execute(module, b'0' * 64, public, region)
    infinite = bytes(wasmtime.wat2wasm('(module (memory (export "memory") 1) (func (export "run") (param i32 i32) (result i32) (loop br 0) i32.const 0))'))
    with pytest.raises(wasmtime.Trap, match="fuel"):
        execute(infinite, signer.sign(infinite), public, region, fuel=100)
    oversized = bytes(wasmtime.wat2wasm('(module (memory (export "memory") 100) (func (export "run") (param i32 i32) (result i32) i32.const 0))'))
    with pytest.raises(wasmtime.WasmtimeError):
        execute(oversized, signer.sign(oversized), public, region)
    imported = bytes(wasmtime.wat2wasm('(module (import "env" "open" (func)) (memory (export "memory") 1) (func (export "run") (param i32 i32) (result i32) i32.const 0))'))
    with pytest.raises(ValueError, match="imports"):
        execute(imported, signer.sign(imported), public, region)


def test_real_local_match_scoped_execution_replay_and_tampering():
    vectors = np.random.default_rng(42).normal(0, 0.1, (40, 3)).astype(np.float32)
    signer = Ed25519PrivateKey.generate()
    key = b'research-only-key-32-bytes-long!!!'
    node = LocalNode(vectors, [vectors[0]], key, signer.public_key().public_bytes_raw())
    code, _ = local_signature(vectors, vectors[0])
    offer = envelope({"type": "OFFER", "query_ref": "query", "hash": code}, key)
    match = open_envelope(node.handle(offer), key)["payload"]
    assert len(match["regions"]) == 1
    region_ref = match["regions"][0]
    expected_result = sum(np.ascontiguousarray(vectors[node.grants[region_ref][2]], dtype="<f4").tobytes())
    with pytest.raises(ValueError, match="Replay"):
        node.handle(offer)
    tampered = json.loads(offer)
    tampered["body"]["peer"] = "attacker"
    with pytest.raises(ValueError, match="Authentication"):
        node.handle(json.dumps(tampered).encode())
    module = count_module()
    request = {"type": "EXECUTE", "query_ref": "query", "region_ref": region_ref,
               "module": base64.b64encode(module).decode(), "signature": base64.b64encode(signer.sign(module)).decode()}
    result = open_envelope(node.handle(envelope(request, key)), key)["payload"]
    assert int.from_bytes(base64.b64decode(result["result"]), "little", signed=True) == expected_result
    with pytest.raises(ValueError, match="consumed"):
        node.handle(envelope(request, key))


def test_node_rejects_malformed_peer_and_query_fields():
    vectors = np.eye(4, dtype=np.float32)
    key = b'research-only-key-32-bytes-long!!!'
    signer = Ed25519PrivateKey.generate()
    node = LocalNode(vectors, [vectors[0]], key, signer.public_key().public_bytes_raw())
    malformed = envelope({"type": "OFFER", "query_ref": "", "hash": "0" * 64}, key)
    with pytest.raises(ValueError, match="Invalid OFFER"):
        node.handle(malformed)
