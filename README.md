# 人事手続きサポート Web アプリ

入社・退社・異動の手続きを支援し、収集情報の保存とスケジュール表の自動生成、タスクのプッシュ通知を行うサンプル実装です。

## 技術スタック

- バックエンド: Python, Flask, SQLAlchemy, SQLite
- フロントエンド: React + Vite
- 通知: Web Push API（VAPIDキー設定が必要）

## セットアップ

### 1) バックエンド

```
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 任意: VAPID キーを環境変数で指定
export VAPID_PUBLIC_KEY="<Your VAPID PUBLIC KEY>"
export VAPID_PRIVATE_KEY="<Your VAPID PRIVATE KEY>"

python server/app.py
# http://localhost:5000/api/health で ok が返れば起動成功
```

データベースは `instance/app.sqlite3` に作成されます。

### 2) フロントエンド

```
cd frontend
npm install
npm run dev
# http://localhost:5173 を開く（/api は 5000 にプロキシ）
```

ブラウザで「通知の許可」を行い、サービスワーカー登録後に `/api/webpush/public_key` から公開鍵を取得して購読します。公開鍵が空の場合は購読が無効になります。

## 使い方

1. 画面上部で区分（入社/退社/異動）を選び、フォームに必要事項を入力して「登録」。
2. 「従業員一覧」から対象を選ぶとスケジュール表が表示されます。進捗（未完了/進行中/完了）を変更可能。
3. 「プッシュ通知を登録」で購読を保存します（従業員紐付け）。
4. 「24時間以内の期限を通知」で、24時間以内に期日を迎えるタスクへ通知送信を試行します。

## API 概要

- `POST /api/employees/onboarding` 入社登録＋タスク自動生成
- `POST /api/employees/offboarding` 退社更新＋タスク自動生成
- `POST /api/employees/transfer` 異動更新＋タスク自動生成
- `GET /api/employees` / `GET /api/employees/:id` 従業員参照
- `GET /api/employees/:id/tasks` タスク参照
- `PATCH /api/tasks/:id` タスク更新（進捗/担当者）
- `GET /api/webpush/public_key` VAPID 公開鍵取得
- `POST /api/subscriptions` Push 購読保存
- `POST /api/notify/upcoming` 期限接近タスクの通知送信（hours 指定可）

## 注意事項

- Web Push 送信には VAPID キーが必要です。実運用では `pywebpush` を使い、各ブラウザの Push Service へ送信します。本リポではキー未設定時は送信しません（エラーにはしません）。
- スケジュールの期日は一例です。自社運用に合わせ、`server/app.py` の `generate_*_tasks` を調整してください。
- SQLite のスキーマは初回起動時に自動生成されます。必要に応じてマイグレーション導入をご検討ください（Alembic など）。

