from __future__ import annotations

import json
from pathlib import Path

from app import ledger
from tests.test_utils import write_test_keys


def test_append_and_verify_ok(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    write_test_keys(tmp_path)

    ledger.ensure_ledger_exists()
    new_block = ledger.append_record("sample", "1.0.0", "", "aa" * 32, 10, "a.bin")

    ok, index, reason = ledger.verify_chain()
    assert ok is True
    assert index is None
    assert reason is None
    assert new_block["signing_key_id"]
    assert new_block["signature"]


def test_verify_detects_signature_invalid(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    write_test_keys(tmp_path)

    ledger.ensure_ledger_exists()
    ledger.append_record("sample", "1.0.0", "", "aa" * 32, 10, "a.bin")

    p = Path("data/ledger.json")
    data = json.loads(p.read_text(encoding="utf-8"))
    sig = data["blocks"][-1]["signature"]
    data["blocks"][-1]["signature"] = ("A" if sig[0] != "A" else "B") + sig[1:]
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    ok, index, reason = ledger.verify_chain()
    assert ok is False
    assert index == 1
    assert reason == "signature_invalid"


def test_anchor_regenerated_on_startup(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    write_test_keys(tmp_path)

    ledger.ensure_ledger_exists()
    anchor_path = Path("anchors/latest.json")
    anchor_path.unlink()

    ledger.ensure_ledger_exists()
    assert anchor_path.exists()
