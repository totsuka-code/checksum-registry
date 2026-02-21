# Ledger 仕様書 v0.1（確定版）

本仕様は `data/ledger.json` の唯一の正規仕様である。

## 1. ファイルパス
- 固定パス: `data/ledger.json`

## 2. トップレベル構造
```json
{
  "schema_version": "0.1",
  "hash_algorithm": "sha256",
  "canonical_json": "JCS-STRICT",
  "blocks": []
}
```

- `schema_version`: 固定値 `"0.1"`
- `hash_algorithm`: 固定値 `"sha256"`
- `canonical_json`: 固定値 `"JCS-STRICT"`
- `blocks`: ブロック配列（先頭は必ずgenesis）

## 3. ブロック定義

## 3.1 共通フィールド
```json
{
  "index": 0,
  "timestamp_utc": "2026-02-21T00:00:00Z",
  "prev_hash": "0000000000000000000000000000000000000000000000000000000000000000",
  "entry": {},
  "block_hash": "..."
}
```

- `index`: 0始まり連番（欠番禁止）
- `timestamp_utc`: UTC ISO8601、秒精度、`Z`終端
- `prev_hash`: 64桁16進小文字
- `entry`: genesis または record
- `block_hash`: 当該ブロック本文のSHA-256（64桁16進小文字）

## 3.2 genesisブロック（固定）
- `blocks[0]` は必ずgenesis
- `index = 0`
- `prev_hash = "0"*64`
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

## 5. Canonical JSON（JCS-STRICT）
- オブジェクトキーは辞書順（昇順）で出力
- 余分な空白・改行を入れない
- 文字列はJSON標準エスケープ
- 数値はJSON数値表現（指数表記禁止、整数は整数のまま）
- 文字コードはUTF-8
- 同一入力から同一バイト列を必ず生成すること

## 6. チェーン整合性
- `blocks[i].prev_hash == blocks[i-1].block_hash`（i>=1）
- 各ブロックで `block_hash == SHA256(canonical_json(block_body))`
- `index` は `0..n-1` で連続
- genesis の `prev_hash` は必ず `"0"*64`

## 7. 追記のみ制約
- 許可操作は `blocks` 末尾への追加のみ
- 既存ブロックの編集・削除は仕様違反
- 更新API・削除APIは提供しない
