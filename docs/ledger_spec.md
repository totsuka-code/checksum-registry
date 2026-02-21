# Ledger 仕様書 v0.2（実装同期版）

## 1. ファイル
- 台帳: `data/ledger.json`
- アンカー: `anchors/latest.json`

## 2. ledger.json 構造
```json
{
  "schema_version": "0.2",
  "hash_algorithm": "sha256",
  "signature_algorithm": "ed25519",
  "canonical_json": "JCS-STRICT",
  "blocks": []
}
```

## 3. ブロック構造
```json
{
  "index": 0,
  "timestamp_utc": "2026-02-21T00:00:00Z",
  "prev_hash": "000...000",
  "entry": {},
  "block_hash": "64hex...",
  "signing_key_id": "16hex",
  "signature": "base64..."
}
```

- genesis/record ともに `signing_key_id`, `signature` 必須。
- `signing_key_id` は公開鍵DERのSHA-256先頭16桁。

## 4. ハッシュ/署名
- `block_hash`: block_body（`index,timestamp_utc,prev_hash,entry`）のみを canonical JSON 化して SHA-256。
- 署名対象: `block_hash` の hex を bytes 化した32バイト。
- 署名アルゴリズム: Ed25519。
- `signature`: base64 文字列。

## 5. 検証規則
- 連番: `index == 配列位置`
- 連結: `prev_hash == 直前block_hash`
- block_hash再計算一致
- genesis妥当性
- 署名存在/鍵ID一致/署名検証成功

## 6. verify reason 値
- `invalid_genesis`
- `index_mismatch`
- `prev_hash_mismatch`
- `block_hash_mismatch`
- `signature_missing`
- `signature_invalid`
- `unknown_key`

## 7. anchors/latest.json
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

- 台帳保存時に更新。
- 欠落時は起動処理で再生成。
