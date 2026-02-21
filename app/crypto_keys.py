from __future__ import annotations

import base64
import hashlib
import os
import stat
import sys
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey


def load_public_key(path: str = "keys/public_key.pem") -> Ed25519PublicKey:
    pem = Path(path).read_bytes()
    key = serialization.load_pem_public_key(pem)
    if not isinstance(key, Ed25519PublicKey):
        raise TypeError("public key is not Ed25519")
    return key


def load_private_key(path: str = "keys/private_key.pem") -> Ed25519PrivateKey:
    validate_private_key_permissions(path)
    pem = Path(path).read_bytes()
    key = serialization.load_pem_private_key(pem, password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise TypeError("private key is not Ed25519")
    return key


def validate_private_key_permissions(path: str = "keys/private_key.pem") -> None:
    private_path = Path(path)
    if not private_path.exists():
        raise FileNotFoundError(f"private key not found: {path}")

    # Windows ACL is not reliably represented by POSIX mode bits.
    if sys.platform.startswith("win"):
        return

    mode = stat.S_IMODE(os.stat(private_path).st_mode)
    # Disallow group/other permissions on private key (e.g. 600 only).
    if mode & 0o077:
        raise PermissionError(
            f"insecure private key permissions: {oct(mode)} (expected no group/other access)"
        )


def key_id_from_public_key(pubkey: Ed25519PublicKey) -> str:
    der = pubkey.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return hashlib.sha256(der).hexdigest()[:16]


def sign_block_hash(private_key: Ed25519PrivateKey, block_hash_hex: str) -> tuple[str, str]:
    block_hash_bytes = bytes.fromhex(block_hash_hex)
    if len(block_hash_bytes) != 32:
        raise ValueError("block_hash_hex must be 32 bytes (64 hex chars)")

    signature = private_key.sign(block_hash_bytes)
    signature_b64 = base64.b64encode(signature).decode("ascii")
    signing_key_id = key_id_from_public_key(private_key.public_key())
    return signature_b64, signing_key_id


def verify_block_hash(
    public_key: Ed25519PublicKey,
    block_hash_hex: str,
    signature_b64: str,
) -> bool:
    try:
        block_hash_bytes = bytes.fromhex(block_hash_hex)
        if len(block_hash_bytes) != 32:
            return False

        signature = base64.b64decode(signature_b64, validate=True)
        public_key.verify(signature, block_hash_bytes)
        return True
    except (ValueError, InvalidSignature):
        return False
