from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LEDGER_PATH = Path("data/ledger.json")
GENESIS_PREV_HASH = "0" * 64


def _utc_now_iso8601_seconds() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _canonical_json_bytes(obj: Any) -> bytes:
    # docs/ledger_spec.md: JCS-STRICT equivalent for this scope (sorted keys, compact, UTF-8)
    text = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return text.encode("utf-8")


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _build_genesis_block(timestamp_utc: str) -> dict[str, Any]:
    body = {
        "index": 0,
        "timestamp_utc": timestamp_utc,
        "prev_hash": GENESIS_PREV_HASH,
        "entry": {"type": "genesis"},
    }
    return {
        **body,
        "block_hash": _sha256_hex(_canonical_json_bytes(body)),
    }


def ensure_ledger_exists() -> None:
    if LEDGER_PATH.exists():
        return

    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    genesis = _build_genesis_block(_utc_now_iso8601_seconds())
    ledger = {
        "schema_version": "0.1",
        "hash_algorithm": "sha256",
        "canonical_json": "JCS-STRICT",
        "blocks": [genesis],
    }

    LEDGER_PATH.write_text(
        json.dumps(ledger, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
