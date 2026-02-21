# 運用Runbook v0.2（確定版）

## 1. 運用対象
- 台帳: `data/ledger.json`
- 最新アンカー: `anchors/latest.json`
- 公開鍵: `keys/public_key.pem`
- 秘密鍵: `keys/private_key.pem`
- 監査ログ: `logs/audit.log.jsonl`
- バックアップ: `backups/<timestamp>/`

## 2. 日次運用
1. サービス起動確認:
```bash
curl -s http://127.0.0.1:8000/api/v1/health
```
2. 台帳検証:
```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/ledger/verify
```
3. 最新アンカー確認:
```bash
curl -s http://127.0.0.1:8000/api/v1/anchors/latest
```
4. 監査ログ追記確認:
- `logs/audit.log.jsonl` の最終行時刻が直近であること

## 3. バックアップ
### 3.1 作成
```bash
python scripts/backup_registry.py
```

### 3.2 生成物
- `data/ledger.json`
- `anchors/latest.json`（存在時）
- `keys/public_key.pem`（存在時）
- `logs/audit.log.jsonl`（存在時）
- `manifest.json`

### 3.3 作成後検証
1. `backups/<timestamp>/manifest.json` が存在すること
2. `manifest.json` のハッシュ値と実ファイルが一致すること

## 4. 障害復旧
### 4.1 前提
- 原則としてアプリ停止中に復旧を行う

### 4.2 復旧
```bash
python scripts/restore_registry.py backups/<timestamp>
```

公開鍵も戻す場合:
```bash
python scripts/restore_registry.py backups/<timestamp> --restore-public-key
```

### 4.3 復旧後確認
1. 台帳検証:
```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/ledger/verify
```
2. アンカー確認:
```bash
curl -s http://127.0.0.1:8000/api/v1/anchors/latest
```
3. 公開鍵確認:
```bash
curl -s http://127.0.0.1:8000/api/v1/keys/public
```

## 5. 鍵ローテーション
### 5.1 手順
1. 現行状態をバックアップする
```bash
python scripts/backup_registry.py
```
2. 新鍵を生成する（開発運用）
```bash
python scripts/generate_keys.py
```
3. 再起動して起動確認を行う
4. `POST /api/v1/ledger/verify` を実行する
5. 新規レコードを1件登録し、`signing_key_id` が新値であることを確認する

### 5.2 注意
- 既存ブロックの `signing_key_id` は旧鍵IDのままである
- 現行実装は単一信頼鍵を前提とするため、旧鍵IDブロックが存在する場合 `unknown_key` となる
- 本運用では「鍵ローテーション時に新規台帳開始」または「検証対象を鍵境界ごとに分離」を採用する

### 5.3 ロールバック
1. 直前バックアップを復旧
```bash
python scripts/restore_registry.py backups/<timestamp> --restore-public-key
```
2. 台帳検証が `valid=true` であることを確認

## 6. 監査ログ保全
### 6.1 保全方針
- `logs/audit.log.jsonl` は追記専用で運用する
- 定期的にバックアップへ取り込む
- 監査提出時はバックアップの `manifest.json` とセットで保管する

### 6.2 保全手順
1. バックアップを取得する
2. `logs/audit.log.jsonl` の最終行時刻を記録する
3. 提出用コピーを作成し、ハッシュ値を記録する

## 7. インシデント一次対応
1. 事象発生時刻を記録する
2. `POST /api/v1/ledger/verify` 実行結果を保存する
3. `logs/audit.log.jsonl` の該当時刻前後を保全する
4. 新規書き込みを停止する（必要に応じてアプリ停止）
5. 直近バックアップからの復旧可否を判断する
