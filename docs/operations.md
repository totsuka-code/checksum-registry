# 運用手順（バックアップ/復旧）

## 1. バックアップ作成
```bash
python scripts/backup_registry.py
```

生成先: `backups/<timestamp>/`

内容:
- `data/ledger.json`
- `anchors/latest.json`（存在時）
- `keys/public_key.pem`（存在時）
- `logs/audit.log.jsonl`（存在時）
- `manifest.json`

## 2. 復旧
```bash
python scripts/restore_registry.py backups/<timestamp>
```

公開鍵も戻す場合:
```bash
python scripts/restore_registry.py backups/<timestamp> --restore-public-key
```

復旧後:
- 台帳整合性・署名検証を自動実行
- 検証失敗時はエラー終了
