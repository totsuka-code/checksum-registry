# API仕様書 v0.2（実装同期版）

Base URL: `http://127.0.0.1:8000/api/v1`

## 1. 共通
- 文字コード: UTF-8
- 通信方式: ローカルHTTPのみ
- ファイル受信: `multipart/form-data`
- エラー形式（共通）:
```json
{
  "error": {
    "code": "STRING_CODE",
    "message": "message"
  }
}
```

## 2. `GET /health`
- 正常: `200`
```json
{
  "status": "ok"
}
```

## 3. `POST /records/register`
- Form:
- `name` required
- `version` required
- `file` required
- 正常: `201`
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
- エラー:
- `400 INVALID_REQUEST`
- `409 DUPLICATE_NAME_VERSION`
- `500 INTERNAL_ERROR`

## 4. `POST /records/verify`
- Form:
- `name` optional
- `version` optional
- `file` required
- 正常: `200`
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
- 不一致: `404`
```json
{
  "matched": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "no matching record"
  }
}
```
- エラー:
- `400 INVALID_REQUEST`
- `500 INTERNAL_ERROR`

## 5. `GET /records`
- 正常: `200`
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
- エラー:
- `500 INTERNAL_ERROR`

## 6. `POST /ledger/verify`
- 正常: `200`
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
- 改ざん検知: `409`
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
- 内部障害: `500 INTERNAL_ERROR`

## 7. `GET /keys/public`
- 正常: `200`
```json
{
  "key_id": "16hex",
  "public_key_pem": "-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----\n"
}
```
- エラー:
- `404 PUBLIC_KEY_NOT_FOUND`
- `500 INTERNAL_ERROR`

## 8. `GET /anchors/latest`
- 正常: `200`
```json
{
  "schema_version": "0.2",
  "ledger_path": "data/ledger.json",
  "latest_index": 12,
  "block_hash": "64hex...",
  "timestamp_utc": "2026-02-21T12:34:56Z",
  "signing_key_id": "16hex",
  "signature": "base64..."
}
```
- エラー:
- `404 ANCHOR_NOT_FOUND`
- `500 INTERNAL_ERROR`

## 9. 非提供API
- 更新APIは提供しない
- 削除APIは提供しない
- 台帳再生成APIは提供しない
- 外部連携APIは提供しない
