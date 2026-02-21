from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


class RegisterResponse(BaseModel):
    index: int
    name: str
    version: str
    sha256: str
    file_size_bytes: int
    original_filename: str
    timestamp_utc: str
    signing_key_id: str
    signature: str


class VerifyResponse(BaseModel):
    matched: bool
    match_mode: str
    index: int
    name: str
    version: str
    sha256: str
    timestamp_utc: str
    signing_key_id: str | None = None
    signature: str | None = None


class RecordItem(BaseModel):
    index: int
    timestamp_utc: str
    name: str
    version: str
    sha256: str
    file_size_bytes: int
    original_filename: str
    signing_key_id: str | None = None
    signature: str | None = None


class RecordsResponse(BaseModel):
    count: int
    items: list[RecordItem]


class VerifyChecks(BaseModel):
    chain_integrity_valid: bool | None
    signature_valid: bool | None


class LedgerVerifySuccessResponse(BaseModel):
    valid: bool
    checked_blocks: int
    checks: VerifyChecks


class PublicKeyResponse(BaseModel):
    key_id: str
    public_key_pem: str


class AnchorLatestResponse(BaseModel):
    schema_version: str
    ledger_path: str
    latest_index: int
    block_hash: str
    timestamp_utc: str
    signing_key_id: str
    signature: str


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


class LedgerVerifyFailedResponse(BaseModel):
    valid: bool
    checks: VerifyChecks
    error: dict[str, Any]
