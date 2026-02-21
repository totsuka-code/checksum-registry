import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from app.crypto_keys import key_id_from_public_key, load_public_key
from app.hashing import sha256_upload_file
from app.ledger import append_record, ensure_ledger_exists, load_ledger, verify_chain

app = FastAPI(title="Checksum Registry", version="0.2")

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
ANCHOR_PATH = Path("anchors/latest.json")
PUBLIC_KEY_PATH = Path("keys/public_key.pem")


@app.on_event("startup")
def on_startup() -> None:
    # v0.2: 公開鍵は起動必須
    load_public_key(str(PUBLIC_KEY_PATH))
    ensure_ledger_exists()


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html", media_type="text/html; charset=utf-8")


@app.get("/static/app.js")
def app_js() -> FileResponse:
    return FileResponse(STATIC_DIR / "app.js", media_type="application/javascript; charset=utf-8")


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


def _verify_breakdown(valid: bool, reason: str | None) -> dict[str, Any]:
    if valid:
        return {
            "chain_integrity_valid": True,
            "signature_valid": True,
        }

    if reason in {"signature_missing", "signature_invalid"}:
        return {
            "chain_integrity_valid": True,
            "signature_valid": False,
        }

    if reason == "unknown_key":
        return {
            "chain_integrity_valid": None,
            "signature_valid": False,
        }

    if reason in {"invalid_genesis", "index_mismatch", "prev_hash_mismatch", "block_hash_mismatch"}:
        return {
            "chain_integrity_valid": False,
            "signature_valid": None,
        }

    return {
        "chain_integrity_valid": None,
        "signature_valid": None,
    }


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
                "signing_key_id": new_block["signing_key_id"],
                "signature": new_block["signature"],
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
                "signing_key_id": matched_block.get("signing_key_id"),
                "signature": matched_block.get("signature"),
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
                "signing_key_id": block.get("signing_key_id"),
                "signature": block.get("signature"),
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
        checks = _verify_breakdown(ok, reason)
        if ok:
            ledger = load_ledger()
            return JSONResponse(
                status_code=200,
                content={
                    "valid": True,
                    "checked_blocks": len(ledger.get("blocks", [])),
                    "checks": checks,
                },
            )

        return JSONResponse(
            status_code=409,
            content={
                "valid": False,
                "checks": checks,
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


@app.get("/api/v1/keys/public")
def get_public_key() -> JSONResponse:
    try:
        pubkey = load_public_key(str(PUBLIC_KEY_PATH))
        pem = PUBLIC_KEY_PATH.read_text(encoding="utf-8")
        return JSONResponse(
            status_code=200,
            content={
                "key_id": key_id_from_public_key(pubkey),
                "public_key_pem": pem,
            },
        )
    except FileNotFoundError:
        return _error_response(404, "PUBLIC_KEY_NOT_FOUND", "public key not found")
    except Exception:
        return _error_response(500, "INTERNAL_ERROR", "internal server error")


@app.get("/api/v1/anchors/latest")
def get_latest_anchor() -> JSONResponse:
    try:
        if not ANCHOR_PATH.exists():
            return _error_response(404, "ANCHOR_NOT_FOUND", "anchor not found")
        anchor = json.loads(ANCHOR_PATH.read_text(encoding="utf-8"))
        return JSONResponse(status_code=200, content=anchor)
    except Exception:
        return _error_response(500, "INTERNAL_ERROR", "internal server error")

