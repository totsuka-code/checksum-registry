# 受け入れテスト手順 v0.1（確定版）

前提:
- サーバーは `127.0.0.1:8000` で起動済み
- `data/ledger.json` は初期化済み（genesisのみ、または過去テストを消去）
- テスト用ファイル:
- `fixtures/a.bin`
- `fixtures/a_copy.bin`（`a.bin` と同一内容）
- `fixtures/b.bin`（`a.bin` と異なる内容）
- `fixtures/large_1gb.bin`（約1GB）

## 1. 初期状態確認
1. `GET /api/v1/records` を実行する。
2. 期待結果:
- 200
- `count=0`
- `items=[]`

## 2. 新規登録成功
1. `POST /api/v1/records/register` with `name=sample` `version=1.0.0` `file=a.bin`
2. 期待結果:
- 201
- `index=1`
- `sha256` が64桁16進小文字

## 3. 重複登録拒否（name+version）
1. 手順2と同じ `name=sample` `version=1.0.0` で `file=b.bin` を登録する。
2. 期待結果:
- 409
- `error.code=DUPLICATE_NAME_VERSION`

## 4. 一覧反映
1. `GET /api/v1/records`
2. 期待結果:
- 200
- `count=1`
- `items[0].name=sample`
- `items[0].version=1.0.0`
- genesisは含まれない

## 5. 検証成功（name/version指定）
1. `POST /api/v1/records/verify` with `name=sample` `version=1.0.0` `file=a_copy.bin`
2. 期待結果:
- 200
- `matched=true`
- `match_mode=name_version_sha`

## 6. 検証失敗（name/version指定）
1. `POST /api/v1/records/verify` with `name=sample` `version=1.0.0` `file=b.bin`
2. 期待結果:
- 404
- `matched=false`
- `error.code=NOT_FOUND`

## 7. 検証成功（shaのみ）
1. `POST /api/v1/records/register` with `name=sample2` `version=2.0.0` `file=a.bin` を実行する。
2. `POST /api/v1/records/verify` with `name=""` `version=""` `file=a.bin` を実行する。
3. 期待結果:
- 200
- `matched=true`
- `match_mode=sha_only`
- 返却 `index` は `a.bin` を最初に登録したレコード（最小index）

## 8. 台帳検証成功
1. `POST /api/v1/ledger/verify`
2. 期待結果:
- 200
- `valid=true`

## 9. 不正入力（登録）
1. `POST /api/v1/records/register` with `name=""` `version=1.0.0` `file=a.bin`
2. 期待結果:
- 400
- `error.code=INVALID_REQUEST`

## 10. 不正入力（検証）
1. `POST /api/v1/records/verify` with `file` 未指定
2. 期待結果:
- 400
- `error.code=INVALID_REQUEST`

## 11. 大容量ファイル登録（約1GB）
1. `POST /api/v1/records/register` with `name=large` `version=1.0.0` `file=large_1gb.bin`
2. 期待結果:
- 201
- タイムアウトせず完了する
- メモリ使用量がファイル全体読込を前提としない挙動（チャンク計算）であること

## 12. 追記のみ確認
1. API一覧を確認する。
2. 期待結果:
- 更新APIが存在しない
- 削除APIが存在しない
- 登録でのみ台帳末尾にブロックが追加される
