# API仕様書 v0.2（実装同期版）

Base URL: `http://127.0.0.1:8000/api/v1`

## 1. 共通エラー形式
```json
{
  "error": {
    "code": "STRING_CODE",
    "message": "message"
  }
}
```

## 2. `POST /records/register`
- Form: `name` required, `version` required, `file` required
- 201:
```json
{
  "index": 1,
  "name": "sample",
  "version": "1.0.0",
  "sha256": "64hex...",
  "file_size_bytes": 123,
  "original_filename": "a.bin",
  "timestamp_utc": "2026-02-21T12:34:56Z",
  "signing_key_id": "16hex",
  "signature": "base64..."
}
```
- 409: `DUPLICATE_NAME_VERSION`
- 400: `INVALID_REQUEST`

## 3. `POST /records/verify`
- Form: `name` optional, `version` optional, `file` required
- 200:
```json
{
  "matched": true,
  "match_mode": "sha_only",
  "index": 1,
  "name": "sample",
  "version": "1.0.0",
  "sha256": "64hex...",
  "timestamp_utc": "2026-02-21T12:34:56Z",
  "signing_key_id": "16hex",
  "signature": "base64..."
}
```
- 404: `NOT_FOUND`
- 400: `INVALID_REQUEST`

## 4. `GET /records`
- 200:
```json
{
  "count": 1,
  "items": [
    {
      "index": 1,
      "timestamp_utc": "2026-02-21T12:34:56Z",
      "name": "sample",
      "version": "1.0.0",
      "sha256": "64hex...",
      "file_size_bytes": 123,
      "original_filename": "a.bin",
      "signing_key_id": "16hex",
      "signature": "base64..."
    }
  ]
}
```

## 5. `POST /ledger/verify`
- 200:
```json
{
  "valid": true,
  "checked_blocks": 3,
  "checks": {
    "chain_integrity_valid": true,
    "signature_valid": true
  }
}
```
- 409:
```json
{
  "valid": false,
  "checks": {
    "chain_integrity_valid": true,
    "signature_valid": false
  },
  "error": {
    "code": "LEDGER_TAMPERED",
    "message": "block verification failed",
    "index": 2,
    "reason": "signature_invalid"
  }
}
```

## 6. `GET /keys/public`
- 200:
```json
{
  "key_id": "16hex",
  "public_key_pem": "-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----\n"
}
```
- 404: `PUBLIC_KEY_NOT_FOUND`

## 7. `GET /anchors/latest`
- 200: `anchors/latest.json` 相当
- 404: `ANCHOR_NOT_FOUND`

## 8. 非提供API
- 更新/削除/台帳再生成/外部連携APIは提供しない
