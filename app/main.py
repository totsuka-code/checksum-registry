from typing import Any

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse

from app.hashing import sha256_upload_file
from app.ledger import append_record, ensure_ledger_exists, load_ledger, verify_chain

app = FastAPI(title="Checksum Registry", version="0.1")


@app.on_event("startup")
def on_startup() -> None:
    ensure_ledger_exists()


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return """<!doctype html>
<html lang=\"ja\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Checksum Registry v0.1</title>
  </head>
  <body>
    <h1>Checksum Registry v0.1</h1>
  </body>
</html>
"""


@app.get("/api/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def _error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
            }
        },
    )


def _record_blocks(ledger: dict[str, Any]) -> list[dict[str, Any]]:
    blocks = ledger.get("blocks", [])
    records: list[dict[str, Any]] = []
    for block in blocks:
        entry = block.get("entry", {})
        if isinstance(entry, dict) and entry.get("type") == "record":
            records.append(block)
    records.sort(key=lambda x: x.get("index", 0))
    return records


@app.post("/api/v1/records/register")
async def register_record(
    name: str | None = Form(None),
    version: str | None = Form(None),
    file: UploadFile | None = File(None),
) -> JSONResponse:
    if name is None or version is None or file is None:
        return _error_response(400, "INVALID_REQUEST", "invalid request")

    name = name.strip()
    version = version.strip()
    if not name or not version or len(name) > 100 or len(version) > 50:
        return _error_response(400, "INVALID_REQUEST", "invalid request")
    if not file.filename:
        return _error_response(400, "INVALID_REQUEST", "invalid request")

    try:
        ledger = load_ledger()
        records = _record_blocks(ledger)
        duplicate = any(
            block["entry"].get("name") == name and block["entry"].get("version") == version
            for block in records
        )
        if duplicate:
            return _error_response(409, "DUPLICATE_NAME_VERSION", "same name/version already exists")

        sha256_hex, size_bytes = await sha256_upload_file(file)
        new_block = append_record(
            name=name,
            version=version,
            note="",
            file_sha256=sha256_hex,
            file_size_bytes=size_bytes,
            original_filename=file.filename,
        )
        entry = new_block["entry"]
        return JSONResponse(
            status_code=201,
            content={
                "index": new_block["index"],
                "name": entry["name"],
                "version": entry["version"],
                "sha256": entry["file_sha256"],
                "file_size_bytes": entry["file_size_bytes"],
                "original_filename": entry["original_filename"],
                "timestamp_utc": new_block["timestamp_utc"],
            },
        )
    except Exception:
        return _error_response(500, "INTERNAL_ERROR", "internal server error")


@app.post("/api/v1/records/verify")
async def verify_record(
    name: str = Form(""),
    version: str = Form(""),
    file: UploadFile | None = File(None),
) -> JSONResponse:
    if file is None or not file.filename:
        return _error_response(400, "INVALID_REQUEST", "invalid request")

    try:
        name = name.strip()
        version = version.strip()
        sha256_hex, _ = await sha256_upload_file(file)

        ledger = load_ledger()
        records = _record_blocks(ledger)
        matched_block: dict[str, Any] | None = None
        match_mode = ""

        if name and version:
            match_mode = "name_version_sha"
            for block in records:
                entry = block["entry"]
                if (
                    entry.get("name") == name
                    and entry.get("version") == version
                    and entry.get("file_sha256") == sha256_hex
                ):
                    matched_block = block
                    break
        else:
            match_mode = "sha_only"
            for block in records:
                entry = block["entry"]
                if entry.get("file_sha256") == sha256_hex:
                    matched_block = block
                    break

        if matched_block is None:
            return JSONResponse(
                status_code=404,
                content={
                    "matched": False,
                    "error": {
                        "code": "NOT_FOUND",
                        "message": "no matching record",
                    },
                },
            )

        entry = matched_block["entry"]
        return JSONResponse(
            status_code=200,
            content={
                "matched": True,
                "match_mode": match_mode,
                "index": matched_block["index"],
                "name": entry["name"],
                "version": entry["version"],
                "sha256": entry["file_sha256"],
                "timestamp_utc": matched_block["timestamp_utc"],
            },
        )
    except Exception:
        return _error_response(500, "INTERNAL_ERROR", "internal server error")


@app.get("/api/v1/records")
def list_records() -> JSONResponse:
    try:
        ledger = load_ledger()
        records = _record_blocks(ledger)
        items = [
            {
                "index": block["index"],
                "timestamp_utc": block["timestamp_utc"],
                "name": block["entry"]["name"],
                "version": block["entry"]["version"],
                "sha256": block["entry"]["file_sha256"],
                "file_size_bytes": block["entry"]["file_size_bytes"],
                "original_filename": block["entry"]["original_filename"],
            }
            for block in records
        ]
        return JSONResponse(status_code=200, content={"count": len(items), "items": items})
    except Exception:
        return _error_response(500, "INTERNAL_ERROR", "internal server error")


@app.post("/api/v1/ledger/verify")
def verify_ledger() -> JSONResponse:
    try:
        ok, index, reason = verify_chain()
        if ok:
            ledger = load_ledger()
            return JSONResponse(
                status_code=200,
                content={
                    "valid": True,
                    "checked_blocks": len(ledger.get("blocks", [])),
                },
            )

        return JSONResponse(
            status_code=409,
            content={
                "valid": False,
                "error": {
                    "code": "LEDGER_TAMPERED",
                    "message": "block verification failed",
                    "index": index,
                    "reason": reason,
                },
            },
        )
    except Exception:
        return _error_response(500, "INTERNAL_ERROR", "internal server error")
