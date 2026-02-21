from __future__ import annotations

import importlib

from fastapi.testclient import TestClient

from tests.test_utils import write_test_keys


def _create_client(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    write_test_keys(tmp_path)

    import app.ledger as ledger_module
    import app.main as main_module

    importlib.reload(ledger_module)
    importlib.reload(main_module)

    return TestClient(main_module.app)


def test_health_and_keys_public(tmp_path, monkeypatch):
    client = _create_client(tmp_path, monkeypatch)

    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}

    r = client.get("/api/v1/keys/public")
    assert r.status_code == 200
    assert "key_id" in r.json()
    assert "BEGIN PUBLIC KEY" in r.json()["public_key_pem"]


def test_register_then_anchor_latest(tmp_path, monkeypatch):
    client = _create_client(tmp_path, monkeypatch)

    files = {"file": ("a.bin", b"abc", "application/octet-stream")}
    data = {"name": "sample", "version": "1.0.0"}
    r = client.post("/api/v1/records/register", data=data, files=files)
    assert r.status_code == 201

    r = client.get("/api/v1/anchors/latest")
    assert r.status_code == 200
    body = r.json()
    assert body["latest_index"] == 1
    assert "block_hash" in body
    assert "signature" in body


def test_ledger_verify_returns_checks(tmp_path, monkeypatch):
    client = _create_client(tmp_path, monkeypatch)

    r = client.post("/api/v1/ledger/verify")
    assert r.status_code == 200
    body = r.json()
    assert body["valid"] is True
    assert body["checks"]["chain_integrity_valid"] is True
    assert body["checks"]["signature_valid"] is True
