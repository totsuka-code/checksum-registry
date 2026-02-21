from __future__ import annotations

import hashlib
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.ledger import verify_chain

LEDGER_PATH = Path("data/ledger.json")
ANCHOR_PATH = Path("anchors/latest.json")
PUBLIC_KEY_PATH = Path("keys/public_key.pem")
AUDIT_LOG_PATH = Path("logs/audit.log.jsonl")


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).strftime("%Y%m%dT%H%M%SZ")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _copy_atomic(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_suffix(dst.suffix + ".tmp")
    shutil.copy2(src, tmp)
    os.replace(tmp, dst)


def perform_backup(backup_root: Path = Path("backups")) -> Path:
    if not LEDGER_PATH.exists():
        raise FileNotFoundError(f"ledger not found: {LEDGER_PATH}")

    backup_root.mkdir(parents=True, exist_ok=True)
    backup_dir = backup_root / _utc_stamp()
    suffix = 0
    while backup_dir.exists():
        suffix += 1
        backup_dir = backup_root / f"{_utc_stamp()}-{suffix}"
    backup_dir.mkdir(parents=True, exist_ok=False)

    candidates = [LEDGER_PATH, ANCHOR_PATH, PUBLIC_KEY_PATH, AUDIT_LOG_PATH]
    files: dict[str, Any] = {}

    for src in candidates:
        if not src.exists():
            continue
        rel = src.as_posix()
        dst = backup_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        files[rel] = {
            "sha256": _sha256_file(dst),
            "size_bytes": dst.stat().st_size,
        }

    manifest = {
        "created_at_utc": (
            datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        ),
        "files": files,
    }
    (backup_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    return backup_dir


def restore_backup(backup_dir: Path, restore_public_key: bool = False) -> None:
    manifest_path = backup_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"manifest not found: {manifest_path}")

    _ = json.loads(manifest_path.read_text(encoding="utf-8"))

    ledger_backup = backup_dir / LEDGER_PATH.as_posix()
    if not ledger_backup.exists():
        raise FileNotFoundError(f"backup ledger not found: {ledger_backup}")
    _copy_atomic(ledger_backup, LEDGER_PATH)

    anchor_backup = backup_dir / ANCHOR_PATH.as_posix()
    if anchor_backup.exists():
        _copy_atomic(anchor_backup, ANCHOR_PATH)

    if restore_public_key:
        pub_backup = backup_dir / PUBLIC_KEY_PATH.as_posix()
        if pub_backup.exists():
            _copy_atomic(pub_backup, PUBLIC_KEY_PATH)

    ok, index, reason = verify_chain()
    if not ok:
        raise ValueError(f"restored ledger verification failed: index={index}, reason={reason}")
