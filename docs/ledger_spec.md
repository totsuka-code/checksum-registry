# Ledger 仕様書 v0.2（確定版）

本仕様は `data/ledger.json` と `anchors/latest.json` の正規仕様である。

## 1. ファイルパス
- 台帳: `data/ledger.json`
- アンカー: `anchors/latest.json`
- 公開鍵（Trust Anchor）: `keys/public_key.pem`
- 秘密鍵（開発用）: `keys/private_key.pem`

## 2. トップレベル構造（ledger.json）
```json
{
  "schema_version": "0.2",
  "hash_algorithm": "sha256",
  "signature_algorithm": "ed25519",
  "canonical_json": "JCS-STRICT",
  "blocks": []
}
```

- `schema_version`: 固定値 `"0.2"`
- `hash_algorithm`: 固定値 `"sha256"`
- `signature_algorithm`: 固定値 `"ed25519"`
- `canonical_json`: 固定値 `"JCS-STRICT"`
- `blocks`: ブロック配列（先頭は必ず署名付きgenesis）

## 3. ブロック定義

## 3.1 共通フィールド
```json
{
  "index": 0,
  "timestamp_utc": "2026-02-21T00:00:00Z",
  "prev_hash": "0000000000000000000000000000000000000000000000000000000000000000",
  "entry": {},
  "block_hash": "64hex...",
  "signing_key_id": "dev-ed25519-001",
  "signature": "base64..."
}
```

- `index`: 0始まり連番（欠番禁止）
- `timestamp_utc`: UTC ISO8601、秒精度、`Z`終端
- `prev_hash`: 64桁16進小文字
- `entry`: genesis または record
- `block_hash`: 当該ブロック本文のSHA-256（64桁16進小文字）
- `signing_key_id`: 1〜128文字
- `signature`: Ed25519署名（base64文字列）

## 3.2 genesisブロック（固定）
- `blocks[0]` は必ずgenesis
- `index = 0`
- `prev_hash = "0"*64`
- genesis も `signing_key_id` と `signature` を必須とする
- `entry`:
```json
{
  "type": "genesis"
}
```

## 3.3 recordブロック
`entry` は以下:
```json
{
  "type": "record",
  "name": "openssl",
  "version": "3.0.0",
  "file_sha256": "64hex...",
  "file_size_bytes": 123456,
  "original_filename": "openssl-3.0.0.tar.gz"
}
```

制約:
- `type`: 固定値 `"record"`
- `name`: 1〜100文字
- `version`: 1〜50文字
- `file_sha256`: 64桁16進小文字
- `file_size_bytes`: 0以上の整数
- `original_filename`: 1文字以上

## 4. ハッシュ仕様

## 4.1 ファイルSHA-256
- アルゴリズム: SHA-256
- 入力: アップロードファイルの生バイト列
- 読み取り単位: 4 MiB固定
- 出力: 64桁16進小文字

## 4.2 block_hash 計算対象
`block_hash` は以下オブジェクトを canonical JSON 化したUTF-8バイト列の SHA-256:
```json
{
  "index": <int>,
  "timestamp_utc": "<string>",
  "prev_hash": "<64hex>",
  "entry": <object>
}
```
- `block_hash` 自身は計算対象に含めない。

## 5. 署名仕様（Ed25519）
- 署名アルゴリズム: Ed25519
- 署名対象: `block_hash` を16進文字列から復元した32バイト値
- 署名結果: 64バイト署名を base64 文字列化して `signature` に保存
- 検証鍵: `keys/public_key.pem` のみを使用
- 鍵識別子: `signing_key_id` は検証時の照合情報として利用する

## 6. Canonical JSON（JCS-STRICT）
- オブジェクトキーは辞書順（昇順）で出力
- 余分な空白・改行を入れない
- 文字列はJSON標準エスケープ
- 数値はJSON数値表現（指数表記禁止、整数は整数のまま）
- 文字コードはUTF-8
- 同一入力から同一バイト列を必ず生成すること

## 7. チェーン整合性
- `blocks[i].prev_hash == blocks[i-1].block_hash`（i>=1）
- 各ブロックで `block_hash == SHA256(canonical_json(block_body))`
- `index` は `0..n-1` で連続
- genesis の `prev_hash` は必ず `"0"*64`
- 全ブロックで `signature` が公開鍵で検証成功すること

## 8. 追記のみ制約
- 許可操作は `blocks` 末尾への追加のみ
- 既存ブロックの編集・削除は仕様違反
- 更新API・削除APIは提供しない

## 9. 外部アンカー仕様（anchors/latest.json）
```json
{
  "schema_version": "0.2",
  "ledger_path": "data/ledger.json",
  "latest_index": 12,
  "block_hash": "64hex...",
  "timestamp_utc": "2026-02-21T12:34:56Z",
  "signing_key_id": "dev-ed25519-001",
  "signature": "base64..."
}
```

- アンカーは台帳の最新ブロックを示す確定点出力とする。
- 人が別媒体へ転記・貼り付けする用途を前提とする。
- 台帳追記時に常に上書き更新する。

## 10. 互換性
- v0.1（`schema_version: "0.1"`）台帳は署名フィールド欠落のため、v0.2署名検証を実施しない。
- v0.2運用開始時は `schema_version: "0.2"` 台帳を新規作成する。
