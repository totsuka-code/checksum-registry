# Checksum Registry 仕様書 v0.2（実装同期版）

本仕様は現行コード（`app/main.py`, `app/ledger.py`）に同期した確定仕様である。

## 1. システム概要
- アプリ種別: FastAPI + ブラウザUI（単一ページ）
- 利用範囲: ローカル専用
- バインド先: `127.0.0.1` のみ
- 外部通信: なし
- API公開範囲: `/api/v1/*` のみ
- 永続化先:
- 台帳: `data/ledger.json`
- 最新アンカー: `anchors/latest.json`
- 公開鍵: `keys/public_key.pem`（起動必須）
- 秘密鍵: `keys/private_key.pem`（開発用）

## 2. UI構成
- ルート: `/`
- セクション:
- 登録
- 検証
- 一覧
- 台帳検証（整合性/署名検証の内訳表示）
- 最新アンカー表示（コピー操作を含む）

## 3. 起動仕様
1. `keys/public_key.pem` を読み込む。
2. 読み込み失敗時は起動失敗（HTTPサービス開始前に例外）。
3. `keys/private_key.pem` が存在する場合は権限制約を検証する。
4. `data/ledger.json` が無い場合は署名付きgenesisを含むv0.2台帳を新規作成する。
5. `anchors/latest.json` が無い場合は台帳末尾ブロックから再生成する。
6. 監査ログに `startup` イベントを記録する。

## 4. 機能仕様
### 4.1 登録
- API: `POST /api/v1/records/register`
- 入力: `name` 必須、`version` 必須、`file` 必須（multipart/form-data）
- バリデーション:
- `name`/`version` は前後空白を除去する
- `name` は 1..100 文字
- `version` は 1..50 文字
- `file.filename` が空文字の場合は不正
- 重複判定: `name+version` が既存recordと一致で拒否
- 成功: `201`
- エラー:
- 入力不正: `400 INVALID_REQUEST`
- 重複: `409 DUPLICATE_NAME_VERSION`
- その他: `500 INTERNAL_ERROR`

### 4.2 検証
- API: `POST /api/v1/records/verify`
- 入力: `name` 任意、`version` 任意、`file` 必須（multipart/form-data）
- 判定ロジック:
- `name` と `version` が両方非空: `name/version/sha256` 完全一致
- どちらか空: `sha256` 一致のみで最小indexの1件
- 成功: `200`
- 不一致: `404 NOT_FOUND`（`matched: false` を返す）
- 入力不正: `400 INVALID_REQUEST`
- その他: `500 INTERNAL_ERROR`

### 4.3 一覧
- API: `GET /api/v1/records`
- 対象: `entry.type == "record"` のみ（genesis除外）
- 並び順: `index` 昇順
- 成功: `200`
- 障害: `500 INTERNAL_ERROR`

### 4.4 台帳検証
- API: `POST /api/v1/ledger/verify`
- 成功: `200`
- `valid: true`
- `checked_blocks: blocks配列長`
- `checks.chain_integrity_valid`
- `checks.signature_valid`
- 改ざん検知: `409 LEDGER_TAMPERED`
- `valid: false`
- `error.index`, `error.reason` を返す

### 4.5 公開鍵情報
- API: `GET /api/v1/keys/public`
- 成功: `200`（`key_id`, `public_key_pem`）
- 公開鍵欠落: `404 PUBLIC_KEY_NOT_FOUND`
- その他: `500 INTERNAL_ERROR`

### 4.6 最新アンカー
- API: `GET /api/v1/anchors/latest`
- 成功: `200`（`anchors/latest.json` 相当）
- 欠落: `404 ANCHOR_NOT_FOUND`
- その他: `500 INTERNAL_ERROR`

## 5. 非機能要件
- SHA-256計算は `4,194,304 bytes (4 MiB)` 固定チャンク
- 文字コードは UTF-8 固定
- 台帳更新は追記のみ（既存ブロックの更新・削除APIは提供しない）
- 台帳/アンカー保存は `tmp -> atomic rename` で行う
