# 利用者ガイド

PageWatchは、SwiftUIとFastAPIを組み合わせたWebページ差分監視の学習用ソースです。このガイドではローカルでAPIを動かし、iPhoneアプリを確認し、本番相当の検証へ進む順番を説明します。

## 最初に知っておくこと

- 完成済み・公開済みアプリではありません。
- 実機およびTestFlightでの最終確認は未完了です。
- 公開にはRailway、Apple Developer、プライバシー文書等の追加設定と確認が必要です。
- 対象URLの利用規約、robots.txt、権利、アクセス負荷、法令を確認する責任は利用者にあります。
- 個別サポート、審査代行、公開代行は含まれません。

## 1. 同梱物を確認する

```text
app/                 FastAPI、Worker、Cron
alembic/             DBマイグレーション
ios/                 SwiftUIアプリとXcodeGen設定
docs/                実装手順、配置図、詳細設計、テスト仕様
sales/               利用条件、FAQ、配布用資料
Dockerfile
Procfile
railway.toml
requirements.txt
README.md
```

最初に `sales/COMMERCIAL_LICENSE_JA.md` と `sales/FAQ_JA.md` を確認してください。

## 2. FastAPIをローカル起動する

DockerfileはPython 3.12を使用しています。READMEの最短手順は次のとおりです。

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=sqlite:///./pagewatch.db
alembic upgrade head
uvicorn app.main:app --reload
```

ブラウザで `http://127.0.0.1:8000/docs` を開き、API仕様を確認します。

別のターミナルでWorkerを起動します。

```bash
source .venv/bin/activate
export DATABASE_URL=sqlite:///./pagewatch.db
python -m app.worker
```

テストには、利用規約とrobots.txtで確認が許可されたURLだけを使ってください。

## 3. iPhoneアプリを生成する

現在のプロジェクト設定はiOS 17.0以上、Xcode 26.0、Swift 5.9を指定しています。MacへXcodeとXcodeGenを用意し、次を実行します。

```bash
cd ios
xcodegen generate
open PageWatch.xcodeproj
```

Debugでは `127.0.0.1:8000` のAPIを使用します。Mac上のAPIへ実機から接続する場合は、ネットワーク、ATS、ファイアウォール等の追加調整が必要になる場合があります。

## 4. コードを読むおすすめ順

1. `docs/02_配置図.md` で全体構成を確認
2. `app/main.py` でAPIの入口を確認
3. `app/models.py` で保存データを確認
4. `app/services/` でURL確認、取得、差分処理を確認
5. `app/worker.py` と `app/jobs/` で非同期処理を確認
6. `ios/PageWatch/` でAPI通信、Keychain、画面を確認

## 5. Railwayで本番相当の検証をする

公開前には同じリポジトリから次の構成を作ります。

- APIサービス
- 常駐Workerサービス
- Cronサービス
- PostgreSQLサービス

APIには公開ドメインと `/health` のHealthcheckを設定します。WorkerとCronには公開ドメインを付けません。主な設定値は `app/config.py` とRailwayの構成ファイルを確認してください。

本番環境では少なくとも次を設定します。

```text
DATABASE_URL=${{Postgres.DATABASE_URL}}
ENVIRONMENT=production
DEVICE_TOKEN_PEPPER=32文字以上のランダム値
```

`DEVICE_TOKEN_PEPPER` やデータベース接続情報をGit、ログ、スクリーンショットへ残さないでください。

## 6. Release用API URLを設定する

`ios/Config/Release.xcconfig` の仮URLを、検証用Railway APIのHTTPS URLへ置き換えます。置換後にDebugとReleaseの双方で、登録、一覧、詳細、停止、再開、削除、データ一括削除を確認してください。

## 7. TestFlight前の必須作業

- Apple DeveloperのTeam、署名、Provisioningを設定
- 独自のBundle ID、表示名、アイコンを設定
- Release用API URLを確定
- 実機で新規インストール、通信、Keychain、再起動、削除を確認
- プライバシーポリシー、利用規約、サポートURLを正式なものへ置換
- 対象URLの利用条件と削除依頼への対応方針を決定
- Railwayのバックアップ、ログ、費用、障害時対応を確認
- TestFlightで内部テストを完了

このリポジトリの現時点では、上記の最終確認は完了していません。

## 更新とサポート

更新時はデータベースと設定をバックアップし、差分とマイグレーションを検証環境で確認してください。個別の導入、質問対応、改修、App Store審査対応は含まれません。

