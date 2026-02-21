# 鍵管理手順 v0.2（確定版）

本手順は Checksum Registry v0.2 の鍵生成・配置・運用に関する確定手順である。

## 1. 鍵ファイル
- 公開鍵: `keys/public_key.pem`
- 秘密鍵（開発用）: `keys/private_key.pem`

要件:
- `keys/public_key.pem` は必須。存在しない場合は起動失敗とする。
- `keys/private_key.pem` はリポジトリにコミットしない。
- `.gitignore` に `keys/private_key.pem` を追加する。

## 2. 鍵生成（開発用）
実行ディレクトリ: リポジトリルート

1. ディレクトリ作成:
```bash
mkdir -p keys
```

2. Ed25519秘密鍵生成:
```bash
openssl genpkey -algorithm Ed25519 -out keys/private_key.pem
```

3. 公開鍵抽出:
```bash
openssl pkey -in keys/private_key.pem -pubout -out keys/public_key.pem
```

4. 権限設定（可能な環境では必須）:
- `keys/private_key.pem` は管理者・実行ユーザーのみ読取可能にする。

## 3. signing_key_id の決定
- 形式: 1〜128文字の固定識別子
- 例: `dev-ed25519-001`
- 同一公開鍵を使う期間は同一 `signing_key_id` を使用する。

## 4. 運用ルール
- 署名時は必ず `keys/private_key.pem` を使用する。
- 検証時は必ず `keys/public_key.pem` を使用する。
- 公開鍵ローテーション時は以下を実施する:
1. 新鍵ペア生成
2. `keys/public_key.pem` を新公開鍵に置換
3. `signing_key_id` を新IDに更新
4. ローテーション境界を運用記録へ残す

## 5. バックアップ
- `keys/private_key.pem` は暗号化された別媒体へバックアップする。
- 平文秘密鍵をメール・チャットへ貼り付けない。
- 紛失時は即時ローテーションする。

## 6. 起動前チェック
1. `keys/public_key.pem` が存在する。
2. `keys/public_key.pem` がPEM形式で読み取れる。
3. `keys/private_key.pem` は必要時のみ存在し、通常運用ではアクセス制限されている。

## 7. トラブルシュート
- 公開鍵未配置エラー:
1. `keys/public_key.pem` の配置を確認
2. 改行コード崩れがある場合は再生成

- 署名検証失敗:
1. `signing_key_id` と実際の公開鍵運用履歴を照合
2. `block_hash` の算出条件（canonical JSON）を照合
3. base64の欠損・改行混入を確認

## 8. 監査観点
- 監査時は以下を提示する:
- `keys/public_key.pem` の配布履歴
- `signing_key_id` の変更履歴
- `anchors/latest.json` の保管履歴（別媒体コピー含む）
