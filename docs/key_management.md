# 鍵管理手順 v0.2（実装同期版）

## 1. 鍵ファイル
- 公開鍵: `keys/public_key.pem`（起動必須）
- 秘密鍵: `keys/private_key.pem`（`.gitignore` 対象）

## 2. 生成
```bash
python scripts/generate_keys.py
```

## 3. key_id
- `key_id` は公開鍵DERのSHA-256先頭16桁。

## 4. 運用
- 署名: `keys/private_key.pem`
- 検証: `keys/public_key.pem`
- 公開鍵が欠落/不正なら起動失敗。

## 5. ローテーション
1. 新鍵生成
2. `keys/public_key.pem` 置換
3. 新しい `key_id` を運用記録に残す

## 6. セキュリティ
- 秘密鍵のGit管理禁止
- 秘密鍵を平文共有しない
