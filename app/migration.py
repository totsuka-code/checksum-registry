from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.crypto_keys import load_private_key, sign_block_hash
from app.ledger import (
    CANONICAL_JSON_LABEL,
    GENESIS_PREV_HASH,
    HASH_ALGORITHM,
    SIGNATURE_ALGORITHM,
    _atomic_write_json,
    _build_block_hash_from_body,
)


def _extract_v01_records(v01_ledger: dict[str, Any]) -> list[dict[str, Any]]:
    blocks = v01_ledger.get("blocks", [])
    out: list[dict[str, Any]] = []
    for block in blocks:
        entry = block.get("entry", {})
        if isinstance(entry, dict) and entry.get("type") == "record":
            out.append(
                {
                    "timestamp_utc": block["timestamp_utc"],
                    "entry": {
                        "type": "record",
                        "name": entry["name"],
                        "version": entry["version"],
                        "file_sha256": entry["file_sha256"],
                        "file_size_bytes": entry["file_size_bytes"],
                        "original_filename": entry["original_filename"],
                    },
                }
            )
    return out


def _sign_block_body(body: dict[str, Any]) -> dict[str, Any]:
    private_key = load_private_key()
    block_hash = _build_block_hash_from_body(body)
    signature, key_id = sign_block_hash(private_key, block_hash)
    return {
        **body,
        "block_hash": block_hash,
        "signing_key_id": key_id,
        "signature": signature,
    }


def _build_anchor(ledger_path: Path, ledger: dict[str, Any]) -> dict[str, Any]:
    latest = ledger["blocks"][-1]
    return {
        "schema_version": "0.2",
        "ledger_path": str(ledger_path).replace("\\", "/"),
        "latest_index": latest["index"],
        "block_hash": latest["block_hash"],
        "timestamp_utc": latest["timestamp_utc"],
        "signing_key_id": latest["signing_key_id"],
        "signature": latest["signature"],
    }


def migrate_v01_to_v02(
    src_ledger_path: Path,
    dst_ledger_path: Path,
    dst_anchor_path: Path,
) -> tuple[Path, Path]:
    src = json.loads(src_ledger_path.read_text(encoding="utf-8"))
    if src.get("schema_version") != "0.1":
        raise ValueError("source ledger is not schema_version 0.1")

    records = _extract_v01_records(src)

    blocks: list[dict[str, Any]] = []

    # genesisは移行時刻で再生成し、v0.2署名付きにする
    genesis_body = {
        "index": 0,
        "timestamp_utc": records[0]["timestamp_utc"] if records else "1970-01-01T00:00:00Z",
        "prev_hash": GENESIS_PREV_HASH,
        "entry": {"type": "genesis"},
    }
    genesis = _sign_block_body(genesis_body)
    blocks.append(genesis)

    for i, rec in enumerate(records, start=1):
        body = {
            "index": i,
            "timestamp_utc": rec["timestamp_utc"],
            "prev_hash": blocks[i - 1]["block_hash"],
            "entry": rec["entry"],
        }
        blocks.append(_sign_block_body(body))

    dst_ledger = {
        "schema_version": "0.2",
        "hash_algorithm": HASH_ALGORITHM,
        "signature_algorithm": SIGNATURE_ALGORITHM,
        "canonical_json": CANONICAL_JSON_LABEL,
        "blocks": blocks,
    }

    _atomic_write_json(dst_ledger_path, dst_ledger)
    _atomic_write_json(dst_anchor_path, _build_anchor(dst_ledger_path, dst_ledger))
    return dst_ledger_path, dst_anchor_path
