from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.crypto_keys import (
    key_id_from_public_key,
    load_private_key,
    load_public_key,
    sign_block_hash,
    verify_block_hash,
)

LEDGER_PATH = Path("data/ledger.json")
ANCHOR_PATH = Path("anchors/latest.json")
LOCK_PATH = Path("data/ledger.lock")
GENESIS_PREV_HASH = "0" * 64
SCHEMA_VERSION = "0.2"
HASH_ALGORITHM = "sha256"
SIGNATURE_ALGORITHM = "ed25519"
CANONICAL_JSON_LABEL = "JCS-STRICT"
LOCK_TIMEOUT_SECONDS = 5.0
LOCK_RETRY_SECONDS = 0.05


def _utc_now_iso8601_seconds() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _canonical_json_bytes(obj: Any) -> bytes:
    # docs/ledger_spec.md で定義された canonical JSON 設定
    text = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return text.encode("utf-8")


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _build_block_hash_from_body(block_body: dict[str, Any]) -> str:
    return _sha256_hex(_canonical_json_bytes(block_body))


def _build_block_body(
    index: int,
    timestamp_utc: str,
    prev_hash: str,
    entry: dict[str, Any],
) -> dict[str, Any]:
    return {
        "index": index,
        "timestamp_utc": timestamp_utc,
        "prev_hash": prev_hash,
        "entry": entry,
    }


def _extract_block_body(block: dict[str, Any]) -> dict[str, Any]:
    return {
        "index": block["index"],
        "timestamp_utc": block["timestamp_utc"],
        "prev_hash": block["prev_hash"],
        "entry": block["entry"],
    }


def _build_signed_block(body: dict[str, Any]) -> dict[str, Any]:
    private_key = load_private_key()
    block_hash = _build_block_hash_from_body(body)
    signature_b64, signing_key_id = sign_block_hash(private_key, block_hash)
    return {
        **body,
        "block_hash": block_hash,
        "signing_key_id": signing_key_id,
        "signature": signature_b64,
    }


def _build_genesis_block(timestamp_utc: str) -> dict[str, Any]:
    body = _build_block_body(
        index=0,
        timestamp_utc=timestamp_utc,
        prev_hash=GENESIS_PREV_HASH,
        entry={"type": "genesis"},
    )
    return _build_signed_block(body)


def _empty_ledger() -> dict[str, Any]:
    genesis = _build_genesis_block(_utc_now_iso8601_seconds())
    return {
        "schema_version": SCHEMA_VERSION,
        "hash_algorithm": HASH_ALGORITHM,
        "signature_algorithm": SIGNATURE_ALGORITHM,
        "canonical_json": CANONICAL_JSON_LABEL,
        "blocks": [genesis],
    }


def _atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(payload, encoding="utf-8")
    os.replace(tmp_path, path)


def _acquire_lock() -> int:
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + LOCK_TIMEOUT_SECONDS
    while True:
        try:
            return os.open(str(LOCK_PATH), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise TimeoutError("ledger lock timeout")
            time.sleep(LOCK_RETRY_SECONDS)


def _release_lock(fd: int) -> None:
    try:
        os.close(fd)
    finally:
        try:
            LOCK_PATH.unlink()
        except FileNotFoundError:
            pass


def _build_latest_anchor(ledger: dict[str, Any]) -> dict[str, Any]:
    latest = ledger["blocks"][-1]
    return {
        "schema_version": SCHEMA_VERSION,
        "ledger_path": str(LEDGER_PATH).replace("\\", "/"),
        "latest_index": latest["index"],
        "block_hash": latest["block_hash"],
        "timestamp_utc": latest["timestamp_utc"],
        "signing_key_id": latest["signing_key_id"],
        "signature": latest["signature"],
    }


def load_ledger() -> dict[str, Any]:
    if not LEDGER_PATH.exists():
        ledger = _empty_ledger()
        save_ledger(ledger)
        return ledger

    return json.loads(LEDGER_PATH.read_text(encoding="utf-8"))


def save_ledger(ledger: dict[str, Any]) -> None:
    lock_fd = _acquire_lock()
    try:
        _atomic_write_json(LEDGER_PATH, ledger)
        _atomic_write_json(ANCHOR_PATH, _build_latest_anchor(ledger))
    finally:
        _release_lock(lock_fd)


def append_record(
    name: str,
    version: str,
    note: str,
    file_sha256: str,
    file_size_bytes: int,
    original_filename: str,
) -> dict[str, Any]:
    del note  # ledger_spec.md v0.2のrecord定義にnoteフィールドは存在しない

    ledger = load_ledger()
    ok, index, reason = verify_chain(ledger)
    if not ok:
        raise ValueError(f"invalid ledger before append: index={index}, reason={reason}")

    blocks = ledger["blocks"]
    last_block = blocks[-1]
    next_index = len(blocks)

    entry = {
        "type": "record",
        "name": name,
        "version": version,
        "file_sha256": file_sha256,
        "file_size_bytes": file_size_bytes,
        "original_filename": original_filename,
    }
    body = _build_block_body(
        index=next_index,
        timestamp_utc=_utc_now_iso8601_seconds(),
        prev_hash=last_block["block_hash"],
        entry=entry,
    )
    new_block = _build_signed_block(body)
    blocks.append(new_block)

    save_ledger(ledger)
    return new_block


def verify_chain(ledger: dict[str, Any] | None = None) -> tuple[bool, int | None, str | None]:
    target = load_ledger() if ledger is None else ledger
    blocks = target.get("blocks")
    if not isinstance(blocks, list) or len(blocks) == 0:
        return (False, 0, "invalid_genesis")

    try:
        public_key = load_public_key("keys/public_key.pem")
        expected_key_id = key_id_from_public_key(public_key)
    except Exception:
        return (False, 0, "unknown_key")

    genesis = blocks[0]
    if genesis.get("index") != 0:
        return (False, 0, "invalid_genesis")
    if genesis.get("prev_hash") != GENESIS_PREV_HASH:
        return (False, 0, "invalid_genesis")
    genesis_entry = genesis.get("entry")
    if not isinstance(genesis_entry, dict) or genesis_entry.get("type") != "genesis":
        return (False, 0, "invalid_genesis")

    for i, block in enumerate(blocks):
        if block.get("index") != i:
            return (False, i, "index_mismatch")

        expected_hash = _build_block_hash_from_body(_extract_block_body(block))
        block_hash = block.get("block_hash")
        if block_hash != expected_hash:
            return (False, i, "block_hash_mismatch")

        if i > 0:
            prev_hash = blocks[i - 1].get("block_hash")
            if block.get("prev_hash") != prev_hash:
                return (False, i, "prev_hash_mismatch")

        signature = block.get("signature")
        signing_key_id = block.get("signing_key_id")
        if not isinstance(signature, str) or not signature:
            return (False, i, "signature_missing")
        if not isinstance(signing_key_id, str) or not signing_key_id:
            return (False, i, "signature_missing")
        if signing_key_id != expected_key_id:
            return (False, i, "unknown_key")

        if not verify_block_hash(public_key, block_hash, signature):
            return (False, i, "signature_invalid")

    return (True, None, None)


def ensure_ledger_exists() -> None:
    ledger = load_ledger()
    if not ANCHOR_PATH.exists():
        _atomic_write_json(ANCHOR_PATH, _build_latest_anchor(ledger))
