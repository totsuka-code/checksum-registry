# 性能試験レポート（2026-02-22）

## 1. 試験目的
- 1GBファイルのハッシュ計算
- 連続登録の実行可否
- 改ざん検知の動作確認

## 2. 試験条件
- 対象システム: checksum-registry v0.2（1.0候補）
- 実行環境: ローカルPC（Windows）
- サーバー起動: `uvicorn app.main:app --host 127.0.0.1 --port 8000`
- 使用コマンド:
- `python scripts/perf_hash_benchmark.py .\test_1gb.bin`
- `POST /api/v1/records/register` を連続実行
- `POST /api/v1/ledger/verify`（改ざん前/後）

## 3. 結果
### 3.1 1GBハッシュ試験
- 実施: 完了
- 判定: PASS
- 備考: 実測ログ（`artifacts/perf/.../benchmark.txt`）はクリーンアップ済み

### 3.2 連続登録試験
- 実施: 完了（10件連続）
- 判定: PASS
- 備考: 実測ログ（`register_raw.txt`, `register_time.txt`, `register_summary.txt`）はクリーンアップ済み

### 3.3 改ざん検知試験
- 実施: 完了
- 判定: PASS
- 確認内容:
- 改ざん前: `valid=true`
- 改ざん後: `valid=false` かつ `error.code=LEDGER_TAMPERED`

## 4. 総括
- 1GB処理、連続登録、改ざん検知の機能要件を満たすことを確認。
- 証跡ファイルは環境クリーンアップにより削除済みのため、再提出が必要な場合は再計測する。
