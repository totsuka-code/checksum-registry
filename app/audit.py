from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

AUDIT_LOG_PATH = Path("logs/audit.log.jsonl")


def _utc_now_iso8601_seconds() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def log_event(action: str, status: str, details: dict[str, Any] | None = None) -> None:
    record = {
        "timestamp_utc": _utc_now_iso8601_seconds(),
        "action": action,
        "status": status,
        "details": details or {},
    }
    AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
