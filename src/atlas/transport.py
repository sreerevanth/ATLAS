"""Minimal local QUIC stream transport for the TIP research demonstration."""

import asyncio
import ipaddress
import struct
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from aioquic.asyncio import connect, serve
from aioquic.quic.configuration import QuicConfiguration
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

from atlas.protocol import LocalNode, envelope, local_signature, open_envelope
from atlas.sandbox import count_module
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


def _certificate(directory: Path):
    key = ec.generate_private_key(ec.SECP256R1())
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")])
    now = datetime.now(timezone.utc)
    certificate = (x509.CertificateBuilder().subject_name(subject).issuer_name(subject)
                   .public_key(key.public_key()).serial_number(x509.random_serial_number())
                   .not_valid_before(now - timedelta(minutes=1)).not_valid_after(now + timedelta(days=1))
                   .add_extension(x509.SubjectAlternativeName([x509.DNSName("localhost"),
                                x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]), critical=False)
                   .sign(key, hashes.SHA256()))
    key_path, cert_path = directory / "key.pem", directory / "cert.pem"
    key_path.write_bytes(key.private_bytes(serialization.Encoding.PEM,
                         serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    cert_path.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
    return key_path, cert_path


async def _read_frame(reader):
    size = struct.unpack("!I", await reader.readexactly(4))[0]
    if size > 100000:
        raise ValueError("TIP frame exceeds maximum size")
    return await reader.readexactly(size)


async def _write_frame(writer, message):
    writer.write(struct.pack("!I", len(message)) + message)
    await writer.drain()


async def _exchange(port: int, configuration, packet: bytes):
    async with connect("127.0.0.1", port, configuration=configuration) as protocol:
        reader, writer = await protocol.create_stream()
        await _write_frame(writer, packet)
        writer.write_eof()
        return await _read_frame(reader)


async def demonstration(output: Path):
    """Run two synthetic local nodes over QUIC, then execute signed Wasm locally."""
    import numpy as np

    rng = np.random.default_rng(42)
    vectors = rng.normal(size=(32, 4)).astype(np.float32)
    vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)
    key = b"local-research-key-32-bytes-long!"
    signer = Ed25519PrivateKey.generate()
    node = LocalNode(vectors, [vectors[0]], key, signer.public_key().public_bytes_raw())
    code, _ = local_signature(vectors, vectors[0])
    with tempfile.TemporaryDirectory(dir=output) as temporary:
        key_path, cert_path = _certificate(Path(temporary))
        server_config = QuicConfiguration(is_client=False, alpn_protocols=["atlas-tip/1"])
        server_config.load_cert_chain(str(cert_path), str(key_path))
        server = await serve("127.0.0.1", 0, configuration=server_config,
                             stream_handler=lambda reader, writer: asyncio.create_task(
                                 _handle_stream(reader, writer, node)))
        port = server._transport.get_extra_info("sockname")[1]
        client_config = QuicConfiguration(is_client=True, alpn_protocols=["atlas-tip/1"])
        client_config.verify_mode = 0
        try:
            offer = envelope({"type": "OFFER", "query_ref": "local-demo", "hash": code}, key)
            match = open_envelope(await _exchange(port, client_config, offer), key)["payload"]
            region_ref = match["regions"][0]
            module = count_module()
            request = {"type": "EXECUTE", "query_ref": "local-demo", "region_ref": region_ref,
                       "module": __import__("base64").b64encode(module).decode(),
                       "signature": __import__("base64").b64encode(signer.sign(module)).decode()}
            result = open_envelope(await _exchange(port, client_config, envelope(request, key)), key)["payload"]
            return {"transport": "QUIC", "host": "127.0.0.1", "certificate": "ephemeral self-signed; client verification disabled for loopback demonstration",
                    "synthetic": True, "match_count": len(match["regions"]),
                    "wasm_result_signed_i32": int.from_bytes(__import__("base64").b64decode(result["result"]), "little", signed=True),
                    "server_events": node.events,
                    "warning": "Local integration smoke test; not deployment, identity, security or privacy evidence."}
        finally:
            server.close()


async def _handle_stream(reader, writer, node):
    try:
        request = await _read_frame(reader)
        response = node.handle(request)
        await _write_frame(writer, response)
    except Exception:
        writer.close()
        return
    writer.close()
