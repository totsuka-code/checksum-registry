from __future__ import annotations

import json
from pathlib import Path

from app.ledger import verify_chain
from app.migration import migrate_v01_to_v02
from tests.test_utils import write_test_keys


def test_migrate_v01_to_v02(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    write_test_keys(tmp_path)

    Path("data").mkdir(parents=True, exist_ok=True)

    v01 = {
        "schema_version": "0.1",
        "hash_algorithm": "sha256",
        "canonical_json": "JCS-STRICT",
        "blocks": [
            {
                "index": 0,
                "timestamp_utc": "2026-01-01T00:00:00Z",
                "prev_hash": "0" * 64,
                "entry": {"type": "genesis"},
                "block_hash": "dummy",
            },
            {
                "index": 1,
                "timestamp_utc": "2026-01-02T00:00:00Z",
                "prev_hash": "dummy",
                "entry": {
                    "type": "record",
                    "name": "sample",
                    "version": "1.0.0",
                    "file_sha256": "aa" * 32,
                    "file_size_bytes": 10,
                    "original_filename": "a.bin",
                },
                "block_hash": "dummy2",
            },
        ],
    }
    src = Path("data/ledger_v01.json")
    src.write_text(json.dumps(v01, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    migrate_v01_to_v02(src, Path("data/ledger.json"), Path("anchors/latest.json"))

    migrated = json.loads(Path("data/ledger.json").read_text(encoding="utf-8"))
    assert migrated["schema_version"] == "0.2"
    assert len(migrated["blocks"]) == 2
    assert "signature" in migrated["blocks"][0]
    assert "signing_key_id" in migrated["blocks"][1]

    ok, index, reason = verify_chain(migrated)
    assert ok is True
    assert index is None
    assert reason is None

    anchor = json.loads(Path("anchors/latest.json").read_text(encoding="utf-8"))
    assert anchor["latest_index"] == 1
