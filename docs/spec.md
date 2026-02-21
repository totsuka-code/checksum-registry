# Checksum Registry 仕様書 v0.2（実装同期版）

本仕様は現行実装に合わせた確定仕様である。

## 1. システム概要
- アプリ種別: FastAPI + ブラウザUI（単一ページ）
- 利用範囲: ローカル専用
- バインド先: `127.0.0.1` のみ
- 外部通信: なし
- 永続化:
- 台帳: `data/ledger.json`
- アンカー: `anchors/latest.json`
- 鍵:
- 公開鍵: `keys/public_key.pem`（必須）
- 秘密鍵: `keys/private_key.pem`（開発用）

## 2. 画面構成
- `/` 単一ページ
- セクション:
- 登録
- 検証
- 一覧
- 台帳検証（署名判定表示付き）
- 最新アンカー（表示 + コピー）

## 3. 起動仕様
1. `keys/public_key.pem` を読み込む。
2. 読み込み失敗時は起動失敗。
3. `data/ledger.json` が無ければ署名付きgenesisで新規作成。
4. `anchors/latest.json` が無ければ台帳末尾ブロックから再生成。

## 4. 機能仕様

## 4.1 登録
- 入力: `name`, `version`, `file`
- 成功: `201`
- 重複 `name+version`: `409`
- 不正入力: `400`

## 4.2 検証
- 入力: `name`（任意）, `version`（任意）, `file`
- `name` と `version` が両方非空: `name/version/sha256` 一致を要求
- どちらか空: `sha256` 一致のみ（最小index）
- 不一致: `404`

## 4.3 一覧
- `GET /api/v1/records`
- genesis（index=0）除外
- `index` 昇順

## 4.4 台帳検証
- `POST /api/v1/ledger/verify`
- `valid` に加えて `checks` を返す:
- `checks.chain_integrity_valid`
- `checks.signature_valid`

## 4.5 公開鍵情報
- `GET /api/v1/keys/public`
- `key_id`, `public_key_pem` を返す

## 4.6 最新アンカー
- `GET /api/v1/anchors/latest`
- `anchors/latest.json` 相当を返す

## 5. 非機能
- ハッシュ計算: `4,194,304 bytes (4 MiB)` チャンク
- 文字コード: UTF-8
- APIは `/api/v1` 配下のみ
