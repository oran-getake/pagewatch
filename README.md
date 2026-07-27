# PageWatch

登録したWebページを定期確認し、前回から変わった文章だけを表示するiPhoneアプリです。

このリポジトリには次が含まれます。

- FastAPI API
- PostgreSQLデータモデルとAlembicマイグレーション
- データベース式ジョブキュー
- Webページ取得、SSRF対策、本文抽出、文章差分
- Railway用API・Worker・Cronコマンド
- SwiftUI iPhoneアプリ
- 実装手順、配置図、詳細設計、テスト仕様

## 現在の実装範囲

実装済み:

- 匿名端末トークン発行とKeychain保存
- 1端末5件までのURL登録
- 一覧、詳細、一時停止、再開、削除
- 利用者による匿名端末データの一括削除
- 登録直後・手動・定期確認
- 5分の手動確認間隔
- 文章抽出、スナップショット、追加・削除差分
- robots.txt確認
- 内部IP・認証情報付きURL・非標準ポートの拒否
- Worker停止後に残った実行中ジョブの自動回収
- 取得サイズ、本文サイズ、リダイレクト回数、タイムアウト制限
- iPhoneの一覧、登録、変更詳細、設定画面

公開前に必要:

- Railwayへの4サービス配置（API、Worker、Cron、PostgreSQL）
- Release用API URLの設定
- Apple Developerの署名設定
- 実機・TestFlight確認
- プライバシーポリシー等の正式URLへの置換
- 対象サイトごとの利用規約確認

## 最短のローカル起動

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=sqlite:///./pagewatch.db
alembic upgrade head
uvicorn app.main:app --reload
```

別のターミナルでワーカーを起動します。

```bash
source .venv/bin/activate
export DATABASE_URL=sqlite:///./pagewatch.db
python -m app.worker
```

APIは `http://127.0.0.1:8000/docs` で操作できます。

## iPhoneアプリ

`ios` でXcodeGenを実行してXcodeプロジェクトを生成します。

```bash
cd ios
xcodegen generate
open PageWatch.xcodeproj
```

Debugは `127.0.0.1:8000`、Releaseは
`ios/Config/Release.xcconfig` のRailway URLを使います。

## 文書

- [実装手順](docs/01_実装手順.md)
- [配置図](docs/02_配置図.md)
- [詳細設計書](docs/03_詳細設計書.md)
- [テスト仕様](docs/04_テスト仕様.md)

## 公式資料

- Railway Cron Jobs: https://docs.railway.com/cron-jobs
- Railway Cron・Worker・Queueの選択: https://docs.railway.com/guides/cron-workers-queues
- Railway Healthchecks: https://docs.railway.com/deployments/healthchecks
- Railway Variables: https://docs.railway.com/variables
- Apple Keychain: https://developer.apple.com/documentation/security/keychain-services
