from __future__ import annotations

from pathlib import Path

from app.backup_restore import perform_backup, restore_backup
from app.ledger import append_record, ensure_ledger_exists, verify_chain
from tests.test_utils import write_test_keys


def test_backup_and_restore(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    write_test_keys(tmp_path)

    ensure_ledger_exists()
    append_record("sample", "1.0.0", "", "aa" * 32, 10, "a.bin")

    backup_dir = perform_backup(Path("backups"))
    assert (backup_dir / "manifest.json").exists()
    assert (backup_dir / "data/ledger.json").exists()

    Path("data/ledger.json").unlink()
    if Path("anchors/latest.json").exists():
        Path("anchors/latest.json").unlink()

    restore_backup(backup_dir)

    assert Path("data/ledger.json").exists()
    assert Path("anchors/latest.json").exists()
    ok, index, reason = verify_chain()
    assert ok is True
    assert index is None
    assert reason is None
