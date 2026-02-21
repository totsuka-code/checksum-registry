from __future__ import annotations

import hashlib
from typing import Any

CHUNK_SIZE = 4194304


def sha256_file_path(path: str) -> tuple[str, int]:
    hasher = hashlib.sha256()
    size_bytes = 0

    with open(path, "rb") as f:
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            hasher.update(chunk)
            size_bytes += len(chunk)

    return hasher.hexdigest(), size_bytes


async def sha256_upload_file(upload_file: Any) -> tuple[str, int]:
    hasher = hashlib.sha256()
    size_bytes = 0

    while True:
        chunk = await upload_file.read(CHUNK_SIZE)
        if not chunk:
            break
        hasher.update(chunk)
        size_bytes += len(chunk)

    try:
        await upload_file.seek(0)
    except Exception:
        pass

    return hasher.hexdigest(), size_bytes
