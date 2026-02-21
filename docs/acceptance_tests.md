# 受け入れテスト手順 v0.2（確定版）

前提:
- サーバーは `127.0.0.1:8000` で起動済み
- `keys/public_key.pem` が存在する
- `keys/private_key.pem` は開発用であり、リポジトリ追跡対象外（`.gitignore` 設定済み）
- `data/ledger.json` は v0.2 初期化済み（署名付きgenesisのみ、または過去テストを消去）
- テスト用ファイル:
- `fixtures/a.bin`
- `fixtures/a_copy.bin`（`a.bin` と同一内容）
- `fixtures/b.bin`（`a.bin` と異なる内容）
- `fixtures/large_1gb.bin`（約1GB）

## 1. 鍵前提確認
1. `keys/public_key.pem` を一時的に退避して起動する。
2. 期待結果:
- 起動失敗
- エラーメッセージに公開鍵未配置であることが含まれる
3. `keys/public_key.pem` を戻して再起動する。

## 2. 初期状態確認
1. `GET /api/v1/records` を実行する。
2. 期待結果:
- 200
- `count=0`
- `items=[]`
3. `POST /api/v1/ledger/verify` を実行する。
4. 期待結果:
- 200
- `valid=true`
- 署名付きgenesisで検証成功する

## 3. 新規登録成功
1. `POST /api/v1/records/register` with `name=sample` `version=1.0.0` `file=a.bin`
2. 期待結果:
- 201
- `index=1`
- `sha256` が64桁16進小文字
- `signing_key_id` が返る
- `signature` がbase64文字列で返る

## 4. 重複登録拒否（name+version）
1. 手順3と同じ `name=sample` `version=1.0.0` で `file=b.bin` を登録する。
2. 期待結果:
- 409
- `error.code=DUPLICATE_NAME_VERSION`

## 5. 一覧反映
1. `GET /api/v1/records`
2. 期待結果:
- 200
- `count=1`
- `items[0].name=sample`
- `items[0].version=1.0.0`
- `items[0].signing_key_id` が存在する
- `items[0].signature` が存在する
- genesisは含まれない

## 6. 検証成功（name/version指定）
1. `POST /api/v1/records/verify` with `name=sample` `version=1.0.0` `file=a_copy.bin`
2. 期待結果:
- 200
- `matched=true`
- `match_mode=name_version_sha`
- `signing_key_id` が返る
- `signature` が返る

## 7. 検証失敗（name/version指定）
1. `POST /api/v1/records/verify` with `name=sample` `version=1.0.0` `file=b.bin`
2. 期待結果:
- 404
- `matched=false`
- `error.code=NOT_FOUND`

## 8. 検証成功（shaのみ）
1. `POST /api/v1/records/register` with `name=sample2` `version=2.0.0` `file=a.bin` を実行する。
2. `POST /api/v1/records/verify` with `name=""` `version=""` `file=a.bin` を実行する。
3. 期待結果:
- 200
- `matched=true`
- `match_mode=sha_only`
- 返却 `index` は `a.bin` を最初に登録したレコード（最小index）

## 9. 台帳検証成功
1. `POST /api/v1/ledger/verify`
2. 期待結果:
- 200
- `valid=true`

## 10. アンカー出力確認
1. 登録後に `GET /api/v1/anchors/latest` を実行する。
2. 期待結果:
- 200
- `latest_index` が最新ブロックのindex
- `block_hash` が最新ブロックと一致
- `timestamp_utc` が最新ブロックと一致
- `signing_key_id` が最新ブロックと一致
- `signature` が最新ブロックと一致

## 11. 不正入力（登録）
1. `POST /api/v1/records/register` with `name=""` `version=1.0.0` `file=a.bin`
2. 期待結果:
- 400
- `error.code=INVALID_REQUEST`

## 12. 不正入力（検証）
1. `POST /api/v1/records/verify` with `file` 未指定
2. 期待結果:
- 400
- `error.code=INVALID_REQUEST`

## 13. 大容量ファイル登録（約1GB）
1. `POST /api/v1/records/register` with `name=large` `version=1.0.0` `file=large_1gb.bin`
2. 期待結果:
- 201
- タイムアウトせず完了する
- メモリ使用量がファイル全体読込を前提としない挙動（チャンク計算）であること

## 14. 追記のみ確認
1. API一覧を確認する。
2. 期待結果:
- 更新APIが存在しない
- 削除APIが存在しない
- 登録でのみ台帳末尾にブロックが追加される

## 15. 改ざん検知（署名）
1. `data/ledger.json` の最新ブロック `signature` を1文字改変する。
2. `POST /api/v1/ledger/verify` を実行する。
3. 期待結果:
- 409
- `error.code=LEDGER_TAMPERED`
- `reason=signature_mismatch`

## 16. 改ざん検知（チェーン）
1. `data/ledger.json` の最新ブロック `prev_hash` を改変する。
2. `POST /api/v1/ledger/verify` を実行する。
3. 期待結果:
- 409
- `error.code=LEDGER_TAMPERED`
- `reason=prev_hash_mismatch`

## 17. v0.1互換方針確認
1. v0.1形式の台帳を入力して起動時または検証時の挙動を確認する。
2. 期待結果:
- v0.2としては新規作成運用であることが明示される
- v0.1は署名検証対象外として扱われる
