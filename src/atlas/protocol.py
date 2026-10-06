"""Authenticated bounded local TIP state; no differential privacy claim."""

import base64
import hashlib
import hmac
import json
import secrets
import time

import numpy as np

from atlas.sandbox import execute
from atlas.topology import agreement, landscape, persistence, signature


def canonical(payload) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def envelope(payload: dict, key: bytes, peer: str = "research-peer") -> bytes:
    body = {"version": 1, "peer": peer, "nonce": secrets.token_hex(16), "time": time.time(), "payload": payload}
    return canonical({"body": body, "mac": hmac.new(key, canonical(body), hashlib.sha256).hexdigest()})


def open_envelope(packet: bytes, key: bytes):
    if len(packet) > 100000:
        raise ValueError("Message exceeds size limit")
    decoded = json.loads(packet)
    if set(decoded) != {"body", "mac"}:
        raise ValueError("Invalid envelope")
    expected = hmac.new(key, canonical(decoded["body"]), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(decoded["mac"], expected):
        raise ValueError("Authentication failed")
    body = decoded["body"]
    if set(body) != {"version", "peer", "nonce", "time", "payload"} or body["version"] != 1:
        raise ValueError("Unsupported protocol schema")
    if not isinstance(body["time"], (int, float)) or not np.isfinite(body["time"]) or abs(time.time() - body["time"]) > 60:
        raise ValueError("Expired message")
    if not isinstance(body["nonce"], str) or len(body["nonce"]) != 32:
        raise ValueError("Invalid nonce")
    return body


def local_signature(vectors, query, size=24, bits=64, resolution=64):
    distances = np.linalg.norm(vectors - query, axis=1)
    indices = np.argsort(distances, kind="stable")[:size]
    diagrams = persistence(vectors[indices])["diagrams"]
    return signature(landscape(diagrams, resolution=resolution), bits=bits), indices


class LocalNode:
    def __init__(self, vectors, anchors, key: bytes, trusted_module_key: bytes, budget=100):
        self.key = key
        self.trusted_module_key = trusted_module_key
        self.vectors = np.asarray(vectors, dtype=np.float32)
        self.regions = []
        for anchor in anchors:
            code, indices = local_signature(vectors, anchor)
            self.regions.append((code, indices))
        self.seen = set()
        self.grants = {}
        self.remaining = budget
        self.events = []

    def handle(self, packet: bytes) -> bytes:
        body = open_envelope(packet, self.key)
        if not isinstance(body["peer"], str) or not body["peer"] or len(body["peer"]) > 128:
            raise ValueError("Invalid peer identifier")
        if body["nonce"] in self.seen or self.remaining <= 0:
            raise ValueError("Replay or query budget exhausted")
        self.seen.add(body["nonce"])
        self.remaining -= 1
        payload = body["payload"]
        if payload.get("type") == "OFFER":
            if (set(payload) != {"type", "query_ref", "hash"}
                    or not isinstance(payload["query_ref"], str) or not payload["query_ref"]
                    or len(payload["query_ref"]) > 128 or not isinstance(payload["hash"], str)):
                raise ValueError("Invalid OFFER")
            if len(payload["hash"]) != 64:
                raise ValueError("Invalid hash length")
            matches = []
            for code, indices in self.regions:
                if agreement(code, payload["hash"]) >= 0.9:
                    region_ref = secrets.token_hex(16)
                    self.grants[region_ref] = (body["peer"], payload["query_ref"], indices, time.monotonic() + 60)
                    matches.append(region_ref)
            response = {"type": "MATCH", "query_ref": payload["query_ref"], "regions": matches}
        elif payload.get("type") == "EXECUTE":
            if (set(payload) != {"type", "query_ref", "region_ref", "module", "signature"}
                    or not all(isinstance(payload[key], str) and payload[key]
                               for key in ("query_ref", "region_ref", "module", "signature"))
                    or len(payload["query_ref"]) > 128 or len(payload["region_ref"]) > 128
                    or len(payload["module"]) > 80000 or len(payload["signature"]) > 256):
                raise ValueError("Invalid EXECUTE")
            grant = self.grants.pop(payload["region_ref"], None)
            if grant is None or grant[:2] != (body["peer"], payload["query_ref"]) or grant[3] < time.monotonic():
                raise ValueError("Missing, expired or consumed region grant")
            region = np.ascontiguousarray(self.vectors[grant[2]], dtype="<f4").tobytes()
            result = execute(base64.b64decode(payload["module"], validate=True),
                             base64.b64decode(payload["signature"], validate=True),
                             self.trusted_module_key, region)
            response = {"type": "RESULT", "query_ref": payload["query_ref"], "result": base64.b64encode(result).decode()}
        else:
            raise ValueError("Unknown message type")
        self.events.append({"type": payload["type"], "wire_bytes": len(packet), "response_type": response["type"]})
        return envelope(response, self.key, "node")
