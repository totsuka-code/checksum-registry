# リリースチェックリスト v0.2

## 1. 事前確認
- [ ] `keys/public_key.pem` が配置済み
- [ ] `keys/private_key.pem` はGit追跡対象外
- [ ] `anchors/latest.json` と `data/ledger.json` の整合を確認

## 2. 品質ゲート
- [ ] `python -m py_compile app/main.py app/ledger.py app/crypto_keys.py app/hashing.py app/migration.py`
- [ ] `pytest` が成功
- [ ] `POST /api/v1/ledger/verify` が `valid=true`

## 3. 運用チェック
- [ ] `python scripts/backup_registry.py` でバックアップ作成成功
- [ ] テスト環境で `python scripts/restore_registry.py backups/<timestamp>` 復旧成功
- [ ] `GET /api/v1/anchors/latest` が200を返す

## 4. セキュリティ
- [ ] 公開鍵ローテーション履歴を更新
- [ ] 監査ログ（`logs/audit.log.jsonl`）の保管先を確認

## 5. リリース記録
- [ ] 変更点を `README.md` / `docs` に反映
- [ ] コミットメッセージにフェーズを明記
- [ ] タグ付け（必要時）
