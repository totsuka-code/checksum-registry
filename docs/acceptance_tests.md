# 受け入れテスト手順 v0.2（実装同期版）

## 前提
- `keys/public_key.pem` が存在する
- サーバー起動: `uvicorn app.main:app --host 127.0.0.1 --port 8000`

## 1. 起動要件
1. `keys/public_key.pem` を退避して起動
2. 起動失敗を確認
3. 公開鍵を戻して起動

## 2. 基本API
1. `GET /api/v1/health` が `{"status":"ok"}` を返す
2. `GET /api/v1/keys/public` が `key_id` と PEM を返す

## 3. 登録/検証
1. register 成功（201）
2. 同 `name+version` 再登録で 409
3. verify 成功（name/version指定）
4. verify 成功（sha_only）
5. verify 不一致で 404

## 4. 一覧
1. `GET /api/v1/records`
2. genesis除外・index昇順を確認

## 5. 台帳検証
1. `POST /api/v1/ledger/verify` 成功時:
- `valid=true`
- `checks.chain_integrity_valid=true`
- `checks.signature_valid=true`

2. 署名改ざん後の失敗:
- `valid=false`
- `error.reason=signature_invalid`
- `checks.signature_valid=false`

## 6. アンカー
1. 登録後 `GET /api/v1/anchors/latest` が200
2. `latest_index` と最新ブロック一致
3. `block_hash` と `signature` 一致

## 7. アンカー欠損復旧
1. `anchors/latest.json` を削除
2. サーバー再起動
3. `GET /api/v1/anchors/latest` で200（再生成確認）
