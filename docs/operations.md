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

## 3. v0.1 から v0.2 への移行（オフライン）
1. 旧台帳を `data/ledger_v01.json` として配置
2. 移行実行:
```bash
python scripts/migrate_v01_to_v02.py --src data/ledger_v01.json --dst data/ledger.json --anchor anchors/latest.json
```
3. `POST /api/v1/ledger/verify` で `valid=true` を確認

注意:
- 旧v0.1ブロックはそのまま使用せず、v0.2形式で再署名して再生成する。
- 移行前に必ずバックアップを取得する。
