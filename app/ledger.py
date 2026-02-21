from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LEDGER_PATH = Path("data/ledger.json")
GENESIS_PREV_HASH = "0" * 64
SCHEMA_VERSION = "0.1"
HASH_ALGORITHM = "sha256"
CANONICAL_JSON_LABEL = "JCS-STRICT"


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


def _build_block_body(index: int, timestamp_utc: str, prev_hash: str, entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "index": index,
        "timestamp_utc": timestamp_utc,
        "prev_hash": prev_hash,
        "entry": entry,
    }


def _build_genesis_block(timestamp_utc: str) -> dict[str, Any]:
    body = _build_block_body(
        index=0,
        timestamp_utc=timestamp_utc,
        prev_hash=GENESIS_PREV_HASH,
        entry={"type": "genesis"},
    )
    return {**body, "block_hash": _build_block_hash_from_body(body)}


def _empty_ledger() -> dict[str, Any]:
    genesis = _build_genesis_block(_utc_now_iso8601_seconds())
    return {
        "schema_version": SCHEMA_VERSION,
        "hash_algorithm": HASH_ALGORITHM,
        "canonical_json": CANONICAL_JSON_LABEL,
        "blocks": [genesis],
    }


def _extract_block_body(block: dict[str, Any]) -> dict[str, Any]:
    return {
        "index": block["index"],
        "timestamp_utc": block["timestamp_utc"],
        "prev_hash": block["prev_hash"],
        "entry": block["entry"],
    }


def load_ledger() -> dict[str, Any]:
    if not LEDGER_PATH.exists():
        ledger = _empty_ledger()
        save_ledger(ledger)
        return ledger

    return json.loads(LEDGER_PATH.read_text(encoding="utf-8"))


def save_ledger(ledger: dict[str, Any]) -> None:
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)

    payload = json.dumps(ledger, ensure_ascii=False, indent=2) + "\n"
    tmp_path = LEDGER_PATH.with_suffix(LEDGER_PATH.suffix + ".tmp")
    tmp_path.write_text(payload, encoding="utf-8")
    os.replace(tmp_path, LEDGER_PATH)


def append_record(
    name: str,
    version: str,
    note: str,
    file_sha256: str,
    file_size_bytes: int,
    original_filename: str,
) -> dict[str, Any]:
    del note  # ledger_spec.md v0.1のrecord定義にnoteフィールドは存在しない

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
    new_block = {**body, "block_hash": _build_block_hash_from_body(body)}
    blocks.append(new_block)

    save_ledger(ledger)
    return new_block


def verify_chain(ledger: dict[str, Any] | None = None) -> tuple[bool, int | None, str | None]:
    target = load_ledger() if ledger is None else ledger
    blocks = target.get("blocks")
    if not isinstance(blocks, list) or len(blocks) == 0:
        return (False, 0, "invalid_genesis")

    genesis = blocks[0]
    if genesis.get("index") != 0:
        return (False, 0, "invalid_genesis")
    if genesis.get("prev_hash") != GENESIS_PREV_HASH:
        return (False, 0, "invalid_genesis")
    genesis_entry = genesis.get("entry")
    if not isinstance(genesis_entry, dict) or genesis_entry.get("type") != "genesis":
        return (False, 0, "invalid_genesis")

    expected_genesis_hash = _build_block_hash_from_body(_extract_block_body(genesis))
    if genesis.get("block_hash") != expected_genesis_hash:
        return (False, 0, "invalid_genesis")

    for i, block in enumerate(blocks):
        if block.get("index") != i:
            return (False, i, "index_mismatch")

        expected_hash = _build_block_hash_from_body(_extract_block_body(block))
        if block.get("block_hash") != expected_hash:
            return (False, i, "block_hash_mismatch")

        if i > 0:
            prev_hash = blocks[i - 1].get("block_hash")
            if block.get("prev_hash") != prev_hash:
                return (False, i, "prev_hash_mismatch")

    return (True, None, None)


def ensure_ledger_exists() -> None:
    load_ledger()
