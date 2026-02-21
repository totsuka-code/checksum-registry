# リリースチェックリスト v0.2

## 1. 事前確認
- [x] `keys/public_key.pem` が配置済み
- [x] `keys/private_key.pem` はGit追跡対象外
- [x] `anchors/latest.json` と `data/ledger.json` の整合を確認（起動時再生成仕様）

## 2. 品質ゲート
- [x] `python -m py_compile app/main.py app/ledger.py app/crypto_keys.py app/hashing.py app/migration.py`
- [x] `pytest` が成功
- [x] `POST /api/v1/ledger/verify` が `valid=true`

## 3. 運用チェック
- [x] `python scripts/backup_registry.py` でバックアップ作成成功
- [x] テスト環境で `python scripts/restore_registry.py backups/<timestamp>` 復旧成功
- [x] `GET /api/v1/anchors/latest` が200を返す

## 4. セキュリティ
- [x] 公開鍵ローテーション履歴を更新（Runbookに手順明記）
- [x] 監査ログ（`logs/audit.log.jsonl`）の保管先を確認

## 5. リリース記録
- [x] 変更点を `README.md` / `docs` に反映
- [x] コミットメッセージにフェーズを明記
- [ ] タグ付け（必要時）

## 6. 最終証跡
- [x] 受け入れテスト最終実施ログ: `docs/acceptance_test_run_2026-02-22.md`
- [x] 性能試験レポート: `docs/performance_report_2026-02-22.md`
