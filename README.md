# checksum-registry

ローカル専用の Checksum Registry v0.2 実装です。  
FastAPI + 単一ページUIで、SHA-256台帳・Ed25519署名・最新アンカー出力を提供します。

## 前提
- Python 3.11 以上
- `keys/public_key.pem` が存在すること（起動必須）

## セットアップ
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## 開発用鍵生成
```bash
python scripts/generate_keys.py
```

生成物:
- `keys/private_key.pem`（`.gitignore` 対象）
- `keys/public_key.pem`（追跡対象）

## 起動
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## 主なエンドポイント
- `GET /api/v1/health`
- `POST /api/v1/records/register`
- `POST /api/v1/records/verify`
- `GET /api/v1/records`
- `POST /api/v1/ledger/verify`
- `GET /api/v1/keys/public`
- `GET /api/v1/anchors/latest`

## 監査ログ
- 保存先: `logs/audit.log.jsonl`
- 形式: JSON Lines（1行1イベント）
- 記録対象: startup/register/verify/list/ledger_verify/keys_public/anchors_latest

## 動作確認
1. `http://127.0.0.1:8000/` を開く。  
2. 登録/検証/一覧/台帳検証/最新アンカー表示が動作することを確認する。  
3. `GET /api/v1/ledger/verify` で `checks.signature_valid` が返ることを確認する。  
4. `logs/audit.log.jsonl` にイベントが追記されることを確認する。

## テスト
```bash
pytest
```

## 永続ファイル
- 台帳: `data/ledger.json`
- 最新アンカー: `anchors/latest.json`

補足:
- `anchors/latest.json` が欠落していても、起動時に `data/ledger.json` から自動再生成されます。

## バックアップ/復旧
バックアップ作成:
```bash
python scripts/backup_registry.py
```

復旧:
```bash
python scripts/restore_registry.py backups/<timestamp>
```

公開鍵もバックアップから戻す場合:
```bash
python scripts/restore_registry.py backups/<timestamp> --restore-public-key
```

## v0.1 から v0.2 への移行
```bash
python scripts/migrate_v01_to_v02.py --src data/ledger_v01.json --dst data/ledger.json --anchor anchors/latest.json
```

## 性能確認（ハッシュ）
```bash
python scripts/perf_hash_benchmark.py <target_file>
```
