# 工数管理アプリ

プロジェクトへの要員アサインと月次工数をシミュレーション・管理するWebアプリケーション。

## 機能

| 画面 | 機能 |
|------|------|
| **要員別工数計画** | 要員ごとの月次工数を確認・シミュレーション。プロジェクト行をクリックすると参加要員一覧パネルを表示 |
| **PJ別工数計画** | プロジェクト単位で工数を集計・シミュレーション |
| **シミュレーションモード** | セルを直接編集して工数の増減を試算。保存でDBに反映、リセットで元の計画値に戻す |
| **計画工数CSVアップロード** | Shift-JIS形式の計画工数CSVを取り込み |
| **CSVダウンロード** | 表示中のデータを同形式でエクスポート |
| **案件・プロジェクト管理** | 案件とプロジェクトの紐づけ管理 |
| **設定** | デフォルトの部門・表示期間をlocalStorageに保存 |

## 技術スタック

**バックエンド**
- Python 3.11+
- FastAPI + Uvicorn
- SQLAlchemy 2.x（ORM）
- Alembic（マイグレーション）
- Pydantic v2
- SQLite

**フロントエンド**
- React 19 + TypeScript
- Vite
- Ant Design 5
- Axios
- React Router v7

## 必要な環境

- Python 3.11 以上
- Node.js 18 以上
- Git

## セットアップ

### 1. リポジトリのクローン

```bash
git clone https://github.com/titami0120/project-management-app.git
cd project-management-app
```

### 2. バックエンド

```bash
cd backend

# 仮想環境の作成・有効化
python -m venv venv

# Windows
venv\Scripts\activate
# Mac / Linux
source venv/bin/activate

# 依存パッケージのインストール
pip install -r requirements.txt

# 環境変数ファイルの作成
copy .env.example .env     # Windows
# cp .env.example .env    # Mac / Linux

# DBの初期化（テーブル作成）
alembic upgrade head

# サーバー起動
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

起動確認: http://localhost:8000/health → `{"status":"ok"}`

API ドキュメント: http://localhost:8000/docs

### 3. フロントエンド（別ターミナル）

```bash
cd frontend
npm install
npm run dev
```

アプリ: http://localhost:5173

### 4. 初期データの投入

アプリ起動後、左メニューの「アップロード（計画工数CSV）」から  
`CSVサンプル/計画工数CSVサンプル.csv` をアップロードするとサンプルデータが入ります。

## プロジェクト構成

```
project-management-app/
├── backend/
│   ├── app/
│   │   ├── models/          # SQLAlchemy モデル
│   │   ├── routers/         # FastAPI ルーター
│   │   ├── schemas/         # Pydantic スキーマ
│   │   ├── services/        # ビジネスロジック
│   │   ├── database.py
│   │   └── main.py
│   ├── alembic/             # DBマイグレーション
│   ├── tests/               # pytestテスト
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   └── src/
│       ├── api/             # Axiosクライアント
│       ├── components/      # UIコンポーネント
│       ├── hooks/           # カスタムフック
│       ├── pages/           # ページコンポーネント
│       └── types/           # TypeScript型定義
├── CSVサンプル/              # サンプルデータ
└── README.md
```

## 主なコマンド

### バックエンド

```bash
# テスト実行
pytest

# Lint
ruff check .
```

### フロントエンド

```bash
# テスト実行
npm test

# ビルド
npm run build

# Lint
npm run lint
```

## 環境変数

`backend/.env`

| 変数名 | デフォルト値 | 説明 |
|--------|-------------|------|
| `DATABASE_URL` | `sqlite:///./workload.db` | DBの接続URL |
| `DEBUG` | `false` | SQLのログ出力 |
