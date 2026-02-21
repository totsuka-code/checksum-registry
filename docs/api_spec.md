# API仕様書 v0.2（確定版）

Base URL: `http://127.0.0.1:8000/api/v1`  
通信形式: JSON（ファイル送信は `multipart/form-data`）

## 1. 共通

## 1.1 エラーレスポンス形式
```json
{
  "error": {
    "code": "DUPLICATE_NAME_VERSION",
    "message": "same name/version already exists"
  }
}
```

## 1.2 共通ステータス
- 200: 成功
- 201: 作成成功
- 400: リクエスト不正
- 404: 対象なし
- 409: 競合（重複・台帳不整合）
- 500: サーバー内部エラー

## 1.3 起動前提
- `keys/public_key.pem` が存在しない場合、アプリは起動しない。

## 2. 登録API
- Method/Path: `POST /records/register`
- Content-Type: `multipart/form-data`

リクエスト項目:
- `name` (required, string, 1..100)
- `version` (required, string, 1..50)
- `file` (required, binary)

成功レスポンス（201）:
```json
{
  "index": 3,
  "name": "openssl",
  "version": "3.0.0",
  "sha256": "8f4c...64hex",
  "file_size_bytes": 1234567,
  "original_filename": "openssl-3.0.0.tar.gz",
  "timestamp_utc": "2026-02-21T12:34:56Z",
  "signing_key_id": "dev-ed25519-001",
  "signature": "base64..."
}
```

エラー:
- 409 `DUPLICATE_NAME_VERSION`
```json
{
  "error": {
    "code": "DUPLICATE_NAME_VERSION",
    "message": "same name/version already exists"
  }
}
```
- 400 `INVALID_REQUEST`
- 500 `INTERNAL_ERROR`

## 3. 検証API
- Method/Path: `POST /records/verify`
- Content-Type: `multipart/form-data`

リクエスト項目:
- `name` (optional, string)
- `version` (optional, string)
- `file` (required, binary)

判定仕様:
- `name` と `version` が両方非空: `name/version/sha256` の一致を要求
- `name` または `version` が空: `sha256` 一致のみで判定し、最小 `index` の1件を返す

成功レスポンス（200）:
```json
{
  "matched": true,
  "match_mode": "sha_only",
  "index": 2,
  "name": "libpng",
  "version": "1.6.43",
  "sha256": "6ab1...64hex",
  "timestamp_utc": "2026-02-21T11:00:00Z",
  "signing_key_id": "dev-ed25519-001",
  "signature": "base64..."
}
```

不一致（404）:
```json
{
  "matched": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "no matching record"
  }
}
```

## 4. 一覧API
- Method/Path: `GET /records`
- Query: なし

成功レスポンス（200）:
```json
{
  "count": 2,
  "items": [
    {
      "index": 1,
      "timestamp_utc": "2026-02-21T10:00:00Z",
      "name": "libpng",
      "version": "1.6.43",
      "sha256": "6ab1...64hex",
      "file_size_bytes": 1111,
      "original_filename": "libpng-1.6.43.tar.xz",
      "signing_key_id": "dev-ed25519-001",
      "signature": "base64..."
    },
    {
      "index": 2,
      "timestamp_utc": "2026-02-21T11:00:00Z",
      "name": "zlib",
      "version": "1.3.1",
      "sha256": "7cd2...64hex",
      "file_size_bytes": 2222,
      "original_filename": "zlib-1.3.1.tar.xz",
      "signing_key_id": "dev-ed25519-001",
      "signature": "base64..."
    }
  ]
}
```

仕様:
- genesis（index=0）は `items` に含めない
- 並び順は `index` 昇順固定

## 5. 台帳検証API
- Method/Path: `POST /ledger/verify`
- Request Body: なし

成功（200）:
```json
{
  "valid": true,
  "checked_blocks": 3
}
```

失敗（409）:
```json
{
  "valid": false,
  "error": {
    "code": "LEDGER_TAMPERED",
    "message": "block verification failed",
    "index": 2,
    "reason": "signature_mismatch"
  }
}
```

## 6. アンカー出力API
- Method/Path: `GET /anchors/latest`
- Query: なし
- 目的: 人が別媒体に貼るための最新アンカー取得

成功（200）:
```json
{
  "schema_version": "0.2",
  "ledger_path": "data/ledger.json",
  "latest_index": 2,
  "block_hash": "64hex...",
  "timestamp_utc": "2026-02-21T11:00:00Z",
  "signing_key_id": "dev-ed25519-001",
  "signature": "base64..."
}
```

失敗:
- 404 `ANCHOR_NOT_FOUND`
- 500 `INTERNAL_ERROR`

## 7. 非提供API（明示）
以下は提供しない:
- レコード更新API
- レコード削除API
- 台帳再生成API
- 外部連携API

## 8. v0.1互換方針
- v0.1台帳は署名情報を持たないため、v0.2APIでの署名検証結果保証対象外とする。
- v0.2運用時は新規台帳を作成する。
