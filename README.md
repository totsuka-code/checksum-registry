# checksum-registry

FastAPIベースのローカル専用アプリケーション雛形です。

## 前提
- Python 3.11 以上

## セットアップ
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 起動
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## 動作確認
1. ブラウザで `http://127.0.0.1:8000/` を開き、`Checksum Registry v0.1` が表示されることを確認する。
2. `http://127.0.0.1:8000/api/v1/health` にアクセスし、`{"status":"ok"}` が返ることを確認する。
3. 初回起動時に `data/ledger.json` が生成されることを確認する。
